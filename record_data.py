import time
import sys
import gpiod
import os.path
from hx711 import HX711

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


class RecordLoadCell:
    def __init__(self, dout_pin: int, sck_pin: int):
        # Calibration values to obtain accurate weight
        self.referenceUnit = -1063

        # Connect GPIOD
        self.chip = None
        self.chip = gpiod.chip("0", gpiod.chip.OPEN_BY_NUMBER)

        # Setting HX711 module
        self.hx = HX711(dout = dout_pin, pd_sck = sck_pin, chip = self.chip)
        self.hx.set_reading_format("MSB", "MSB")
        self.hx.set_reference_unit(self.referenceUnit)
        self.hx.reset()
        self.tare()

        # Initialize Variables
        self.record_time = 0.0
        self.record_val = 0.0
        self.total_data = np.array([])
        self.noise_val = []
        self.plot_time = None
        self.plot_val = None
        self.max_val = None
        self.min_val = None
        self.save_address = "/home/soobin/RT_test_data/test"
        self.df = None
        self.i = 1



    def tare(self):
        
        self.hx.tare()
        print("Tare done! Add weight now...")
        time.sleep(1)

    def data_recording(self):
        print("\nCleaning...")
        self.chip.reset()
        time.sleep(0.5)
        print("\nDone!!\n")

        print("Data Postprocessing... \n\nData Length : {}".format(len(self.total_data)))
        self.total_data = np.reshape(self.total_data, (-1,2))
        print("Reshape Data : {}".format(self.total_data.shape))

        for i in range(1, len(self.total_data)-1):
            if i == 1:
                if abs(self.total_data[i-1,1] - self.total_data[i,1]) > 250:
                    self.noise_val.append(i-1)

                elif (abs(self.total_data[i-1,1] - self.total_data[i,1]) > 250 and 
                    abs(self.total_data[i,1] - self.total_data[i+1,1]) > 250) :
                    self.noise_val.append(i)
                
            elif i == len(self.total_data)-1:
                if abs(self.total_data[i,1] - self.total_data[i+1,1]) > 250 :
                    self.noise_val.append(i+1)

                elif (abs(self.total_data[i-1,1] - self.total_data[i,1]) > 250 and 
                    abs(self.total_data[i,1] - self.total_data[i+1,1]) > 250) :
                    self.noise_val.append(i)

            elif (abs(self.total_data[i-1,1] - self.total_data[i,1]) > 250 and 
                    abs(self.total_data[i,1] - self.total_data[i+1,1]) > 250) :
                self.noise_val.append(i)
                
            else:
                pass

        self.total_data = np.delete(self.total_data, self.noise_val, axis=0)

        print("Delete Noise Data : {} // Noise Data Count : {}\n".format(self.total_data.shape, len(self.noise_val)))
        
        self.df = pd.DataFrame(self.total_data)
        
        while os.path.isfile(self.save_address + str(self.i) + ".csv"):
            self.i += 1
        self.df.to_csv(self.save_address + str(self.i) + ".csv", index=False)
        print("Data Saved at {}\n".format(self.save_address + str(self.i) + ".csv"))
        time.sleep(0.5)

        print("Saving Plot figure...")
        self.plot_time = self.total_data[:, 0]
        self.plot_val = self.total_data[:, 1]
        self.max_val = np.max(self.plot_val)
        self.min_val = np.min(self.plot_val)

        plt.plot(self.plot_time, self.plot_val)
        plt.plot(self.plot_time[np.argmax(self.plot_val)], self.plot_val[np.argmax(self.plot_val)], "o", color="Red", label=self.max_val)
        plt.plot(self.plot_time[np.argmin(self.plot_val)], self.plot_val[np.argmin(self.plot_val)], "o", color="Blue", label=self.min_val)
        plt.title("Load Cell Data")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.legend(fontsize=12)
        # plt.show()
        plt.savefig(self.save_address + str(self.i) + ".jpg")
        print("Max value : {} , Min value : {}\n".format(self.max_val, self.min_val))
        print("Figure Saved at {}\n".format(self.save_address + str(self.i) + ".jpg"))


        print("Bye!")
        sys.exit()

    def get_data(self):
        while True:
            try:
                self.record_time = time.time()
                self.record_val = self.hx.get_weight(1)
                self.total_data = np.append(self.total_data, [round(self.record_time,4),round(self.record_val, 2)], axis = 0)
                
                print(f"Weight : {self.record_val:.2f} / Recorded Time : {self.record_time:.4f}")
                time.sleep(0.001)

            except (KeyboardInterrupt, SystemExit):
                self.data_recording()



if __name__ == "__main__":
    rlc = RecordLoadCell(dout_pin = 11, sck_pin = 7)
    rlc.get_data()