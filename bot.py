import time
import cv2
import numpy as np
import psutil
import pywinauto
from pywinauto.application import Application
from pprint import pprint

# WARNING - On multiple screen configuration, pywinauto window.capture_as_image() doesn't work on every screen.

CHEST_REMAINING_TIME_AREA_WIDTH = 75
HOURGLASS_VALUE_THRESHOLD = 0.725
OPEN_VALUE_THRESHOLD = 0.98
TOUCH_TO_OPEN_VALUE_THRESHOLD = 0.7
UNLOCK_BUTTON_VALUE_THRESHOLD = 0.7


class ClashRoyaleBot:
    pid = 0         # bluestacks process id
    window = None   # bluestacks window

    def __init__(self):
        self.get_bluestacks()

    def get_bluestacks(self):
        print('[i] Looking for bluestacks in processes')
        for proc in psutil.process_iter():
            if proc.name() == "Bluestacks.exe":
                bluestacks = Application(backend='uia').connect(process=proc.pid)
                try:
                    # bluestacks spawns two process, only one has a window
                    self.window = bluestacks.windows()[0]
                    self.pid = proc.pid
                    print(f'[+] Bluestacks process and window found - pid: {proc.pid}')
                    return
                except IndexError as e:
                    pass

    def get_screenshot(self):
        self.window.set_focus()
        return self.window.capture_as_image()     

    def __find_in_screen(self, searched_image_name, threshold):
        screen = self.get_screenshot() 
        
        # Convert screen to gray
        np_screen = np.array(screen, dtype = np.uint8)
        gray_screen = cv2.cvtColor(np_screen, cv2.COLOR_BGR2GRAY)

        # Convert searched image to gray and get its width / height
        np_image = cv2.imread(searched_image_name)
        gray_image = cv2.cvtColor(np_image, cv2.COLOR_BGR2GRAY)
        w, h = gray_image.shape[::-1] 

        # Look for searched image in screen
        matches = cv2.matchTemplate(gray_screen, gray_image, cv2.TM_CCOEFF_NORMED)
        
        # Get best match coordinates, check if it's below the threshold
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matches)
        print(f'[i] Search value : {max_val} for object : {searched_image_name}')
        if max_val < threshold:
            return False
        top_left = max_loc
        bottom_right = (top_left[0] + w, top_left[1] + h)
        return (top_left, bottom_right)

    def start_unlocking_chest(self):
        print('[i] Start unlocking chest')      
        try:
            top_left, bottom_right = self.__find_in_screen('touch_to_open.png', TOUCH_TO_OPEN_VALUE_THRESHOLD)
            pywinauto.mouse.click(button='left', coords=(
                self.window.rectangle().left + bottom_right[0], 
                self.window.rectangle().top  + bottom_right[1] + 10
            ))
            time.sleep(1)
        except TypeError as e:
            print('[!] No unlockable chest found')

        try:
            top_left, bottom_right = self.__find_in_screen('unlock_button.png', UNLOCK_BUTTON_VALUE_THRESHOLD)
            pywinauto.mouse.click(button='left', coords=(
                self.window.rectangle().left + bottom_right[0], 
                self.window.rectangle().top  + bottom_right[1] + 10
            ))
            time.sleep(1)
            return True
        except TypeError as e:
            print('[!] No unlock button found')
        return False

    def open_chest(self):
        print('[i] Opening chest')      
        try:
            top_left, bottom_right = self.__find_in_screen('open.png', OPEN_VALUE_THRESHOLD)
        except TypeError as e:
            print('[!] No chest ready for opening')
            return False

        for i in range(0,15):
            pywinauto.mouse.click(button='left', coords=(
                self.window.rectangle().left + bottom_right[0], 
                self.window.rectangle().top  + top_left[1]
            ))
            time.sleep(1)
        return True


    ####################################################################
    # MAYBE IN A FUTURE VERSION : Read the delay for next chest unlock #
    ####################################################################
    # @TODO : 
    # - Characters recognition for time
    # - When time is found, sleep as much seconds before connecting back
    ####################################################################
    def get_next_chest_delay(self):
        print('[i] Getting next chest delay')

        print('[i]Looking for hourglass in screen')
        screen = self.get_screenshot() 
        
        # Convert screen to gray
        np_screen = np.array(screen, dtype = np.uint8)
        gray_screen = cv2.cvtColor(np_screen, cv2.COLOR_BGR2GRAY)

        # Convert hourglass to gray and get its width / height
        np_hourglass = cv2.imread('hourglass.png')
        gray_hourglass = cv2.cvtColor(np_hourglass, cv2.COLOR_BGR2GRAY)
        w, h = gray_hourglass.shape[::-1] 

        # Look for hourglass in screen
        matches = cv2.matchTemplate(gray_screen, gray_hourglass, cv2.TM_CCOEFF_NORMED)
        
        # Get best match coordinates and draw it
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(matches)
        print(f"\t - Best match value : {max_val}")
        if max_val < HOURGLASS_VALUE_THRESHOLD:
            print(f'[!] Hourglass value threshold below {HOURGLASS_VALUE_THRESHOLD}.')
            return False
        hourglass_top_left = max_loc
        hourglass_bottom_right = (hourglass_top_left[0] + w, hourglass_top_left[1] + h)
        cv2.rectangle(np_screen, hourglass_top_left, hourglass_bottom_right, (255, 0, 0), 2)

        # Get the part of the image with the chest time remaining
        time_top_left = (hourglass_bottom_right[0] + 5, hourglass_top_left[1] + 5)
        time_bottom_right = (hourglass_bottom_right[0] + CHEST_REMAINING_TIME_AREA_WIDTH, hourglass_bottom_right[1] - 5)
        cv2.rectangle(np_screen, time_top_left,  time_bottom_right, (0, 0, 255), 2)
        np_time = gray_screen[time_top_left[1]:time_bottom_right[1], time_top_left[0]:time_bottom_right[0]]

        # convert image to black and white
        threshold = 170
        np_time_bw = cv2.threshold(np_time, threshold, 255, cv2.THRESH_BINARY)[1]

        # search for contours in time
        im, contours, hierarchy = cv2.findContours(np_time_bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # sort contours from left to right
        boundingBoxes = [cv2.boundingRect(c) for c in contours]
        (contours, boundingBoxes) = zip(*sorted(zip(contours, boundingBoxes),
                                        key=lambda b:b[1][0]))
        
        for contour in contours:
            # ignore contours with low area
            x,y,w,h = cv2.boundingRect(contour)
            if not(3 <= w <= 12 and 3 <= h <= 11) or w * h < 20:
                continue
            # TODO : extract contour instead of rect
            letter = np_time_bw[y:y+h, x:x+w]
            letter_big = cv2.resize(letter, (0,0), fx=5, fy=5)
            cv2.destroyAllWindows()
            cv2.imshow('Letter', letter_big)
            cv2.waitKey(5000)
            #cv2.drawContours(np_time_bw, [box], 0, (0,255,0), 1)

        # np_time_bw_big = cv2.resize(np_time_bw, (0,0), fx=5, fy=5) 
        # cv2.imshow('Time', np_time_bw_big)
        # cv2.waitKey(100)
        # time.sleep(20)



if __name__=='__main__':
    crb = ClashRoyaleBot()
    while 1:
        crb.open_chest()
        crb.start_unlocking_chest()
        time.sleep(60 * 1) # sleep 1 min
    

