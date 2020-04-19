from PyQt5.QtWidgets import *
from PyQt5 import uic
import nidaqmx
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from nidaqmx.constants import LineGrouping
import time
from nidaqmx.types import CtrTime
import sys, os         
pathname = os.path.dirname(sys.argv[0])        
path=os.path.abspath(pathname)
form_class = uic.loadUiType(path+'\\daq_gui.ui')[0]
# 116 strona
class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.isRun = True
        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlabel("Time [s]")
        self.ax.set_ylabel("Temperature [\u2103]")
        self.y = np.zeros(600)
        self.x = np.zeros(600)
        self.iterator=0
        self.line, = self.ax.plot([0,60], [20,30], "g")
        self.canvas = FigureCanvas(self.fig)
        self.Figure.addWidget(self.canvas)
        self.starten=time.time()
        self.freqSlider.valueChanged.connect(self.updateFreq)
        self.dutySlider.valueChanged.connect(self.updateDuty)
        self.freqSlider2.valueChanged.connect(self.updateFreq2)
        self.dutySlider2.valueChanged.connect(self.updateDuty2)
        self.freq1=self.freqSlider.value()
        self.duty1=self.dutySlider.value()
        self.freq2=self.freqSlider2.value()
        self.duty2=self.dutySlider2.value()
        self.DAQ()

    def updateFreq(self, event):
        self.freqLCD.display(event)
    def updateDuty(self, event):
        self.dutyLCD.display(event)
    def updateFreq2(self, event):
        self.freqLCD2.display(event)
    def updateDuty2(self, event):
        self.dutyLCD2.display(event)

    def drawPlot(self):

        self.line.set_xdata(self.x)
        self.line.set_ydata(self.y)
        self.canvas.draw()
    def DAQ(self):
        global read_task
        global fan_task
        global heat_task
        read_task = nidaqmx.Task()
        fan_task=nidaqmx.Task()
        heat_task=nidaqmx.Task()
        read_task.ai_channels.add_ai_voltage_chan("Dev1/ai1")
        read_task.timing.cfg_samp_clk_timing(rate=10,
                                        sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
                                        samps_per_chan=1)

        fan_task.co_channels.add_co_pulse_chan_freq(counter="Dev1/ctr0",freq=self.freq1, duty_cycle=self.duty1/100)
        fan_task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
        samps_per_chan=1)

        heat_task.co_channels.add_co_pulse_chan_freq(counter="Dev1/ctr1",freq=self.freq2, duty_cycle=self.duty2/100)
        heat_task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,
        samps_per_chan=1)

        fan_task.start()
        fan_task.is_task_done()

        heat_task.start()
        heat_task.is_task_done()
        def callback(task_handle, every_n_samples_event_type,
                     number_of_samples, callback_data):
            global fan_task
            global heat_task
            if(self.freq1!=self.freqSlider.value() or self.duty1!=self.dutySlider.value()):
                self.freq1=self.freqSlider.value()
                self.duty1=self.dutySlider.value()
                fan_task.is_task_done()
                fan_task.stop()
                fan_task.close()
                fan_task=nidaqmx.Task()
                fan_task.co_channels.add_co_pulse_chan_freq(counter="Dev1/ctr0",freq=self.freq1, duty_cycle=self.duty1/100)
                fan_task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,samps_per_chan=1000)
                fan_task.start()
            if(self.freq2!=self.freqSlider2.value() or self.duty2!=self.dutySlider2.value()):
                self.freq2=self.freqSlider2.value()
                self.duty2=self.dutySlider2.value()
                heat_task.is_task_done()
                heat_task.stop()
                heat_task.close()
                heat_task=nidaqmx.Task()
                heat_task.co_channels.add_co_pulse_chan_freq(counter="Dev1/ctr1",freq=self.freq2, duty_cycle=self.duty2/100)
                heat_task.timing.cfg_implicit_timing(sample_mode=nidaqmx.constants.AcquisitionType.CONTINUOUS,samps_per_chan=1000)
                heat_task.start()
                
     
            t = time.time() - self.starten
            old_list=read_task.read(number_of_samples_per_channel=1)
            my_new_list = [i * 100 for i in old_list ]
            self.tempValue.display("{:.1f}".format(float(np.array(my_new_list))))
            self.y = np.append(self.y[1:599],np.array(my_new_list)) 
            self.x=np.linspace(t-60,t,599)
            if t>60: self.ax.set_xlim(t-60, t)
            else: self.ax.set_xlim(0, 60)
            self.ax.set_ylim(0, np.max(self.y)+10)
            self.drawPlot()
            return 0
        
        read_task.register_every_n_samples_acquired_into_buffer_event(1, callback)      
        read_task.start()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()
    read_task.close()
    fan_task.close()
    sys.exit()