import logging
import subprocess
import threading

import wishful_upis as upis
import wishful_framework as wishful_module

__author__ = "Peter Ruckebusch"
__copyright__ = "Copyright (c) 2018, Ugent IDLAB IMEC"
__version__ = "0.1.0"
__email__ = "peter.ruckebusch@ugent.be"


@wishful_module.build_module
class EnvEmuModule(wishful_module.AgentModule):
    def __init__(self):
        super(EnvEmuModule, self).__init__()
        self.log = logging.getLogger('EnvEmuModule')
        self.ee_connected = False
        try:
            ee_node_output = subprocess.check_output(["ls /dev/ee"], universal_newlines=True).strip()
        except FileNotFoundError:
            ee_node_output = ""
        if "/dev/ee" in ee_node_output:
            self.ee_sf_process = subprocess.Popen(['../../experimentation_tools/EnvEmu/connectEE.rb'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.ee_write_process = subprocess.Popen(['../../experimentation_tools/EnvEmu/write_to_ee.rb'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.ee_connected = True
            self.__ee_thread_stop = threading.Event()
            self.__ee_thread = threading.Thread(target=self.__ee_listen, args=(self.__ee_thread_stop,))
            self.__ee_thread.daemon = True
        pass

    @wishful_module.on_start()
    def envemu_module_start(self):
        self.log.info("EnvEmu module start".format())
        self.__ee_thread.start()

    @wishful_module.on_exit()
    def envemu_module_exit(self):
        self.log.info("EnvEmu module exit".format())
        self.ee_write_process().kill()
        self.__ee_thread_stop.set()

    @wishful_module.on_connected()
    def envemu_module_connected(self):
        self.log.info("EnvEmu module connected to global controller".format())

    @wishful_module.on_disconnected()
    def envemu_module_disconnected(self):
        self.log.info("EnvEmu module disconnected from global controller".format())

    @wishful_module.on_first_call_to_module()
    def envemu_module_first_call(self):
        self.log.info("EnvEmu module first call".format())

    def __ee_listen(self, stop_event):
        while not stop_event.is_set():
            self.log.info("%s", self.ee_sf_process.stdout.readline().strip())

    def before_init_energy_harvester(self):
        self.log.info("This function is executed before init_energy_harvester".format())

    def after_init_energy_harvester(self):
        self.log.info("This function is executed after init_energy_harvester".format())

    @wishful_module.before_call(before_init_energy_harvester)
    @wishful_module.after_call(after_init_energy_harvester)
    @wishful_module.bind_function(upis.mgmt.init_energy_harvester)
    def init_energy_harvester(self):
        self.log.info("EE Module init_energy_harvester".format())
        self.log.info("Sending init config".format())
        init_cmd = "EE_MSG_CONFIG_SAMPLER{msgt_am=248, EEMsgConfigSampler_time_us=0, EEMsgConfigSampler_ADCid=4, EEMsgConfigSampler_sampleRate=0, EEMsgConfigSampler_triggerLevel=0, EEMsgConfigSampler_numberOfSamplesReq=0,  EEMsgConfigSampler_samplerReportIDType=0}"
        self.ee_write_process.stdin.write(init_cmd)
        self.ee_write_process.stdin.flush()
        self.log.info("Stopping streamer just in case".format())
        streamer_off_cmd = "EE_MSG_CONFIG_STREAMER{msgt_am=250, EEMsgConfigStreamer_time_us=0, EEMsgConfigStreamer_DACid=1, EEMsgConfigStreamer_sample=0, EEMsgConfigStreamer_harvesterCapacitor=0, EEMsgConfigStreamer_harvester=0, EEMsgConfigStreamer_outerLoopResistor=0, EEMsgConfigStreamer_maxDACvalue = 4095 }"
        self.ee_write_process.stdin.write(streamer_off_cmd)
        self.ee_write_process.stdin.flush()
        return 0

    @wishful_module.bind_function(upis.mgmt.start_energy_harvester)
    def start_energy_harvester(self):
        self.log.info("EE Module start_energy_harvester".format())
        self.log.info("Disabling USB".format())
        disable_usb_cmd = "EE_MSG_SET_GPIO_PIN_STATUS{msgt_am=252, EEMsgSetGPIOPinStatus_time_us=0, EEMsgSetGPIOPinStatus_gpioPinStatus=0x18000000}"
        self.ee_write_process.stdin.write(disable_usb_cmd)
        self.ee_write_process.stdin.flush()
        self.log.info("Start streamer".format())
        streamer_on_cmd = "EE_MSG_CONFIG_STREAMER{msgt_am=250, EEMsgConfigStreamer_time_us=0, EEMsgConfigStreamer_DACid=1, EEMsgConfigStreamer_sample=3550, EEMsgConfigStreamer_harvesterCapacitor=500000, EEMsgConfigStreamer_harvester=0, EEMsgConfigStreamer_outerLoopResistor=0, EEMsgConfigStreamer_maxDACvalue = 4095 }"
        self.ee_write_process.stdin.write(streamer_on_cmd)
        self.ee_write_process.stdin.flush()
        self.log.info("Start sampler".format())
        start_sampler_cmd = "EE_MSG_CONFIG_SAMPLER{msgt_am=248, EEMsgConfigSampler_time_us=0, EEMsgConfigSampler_ADCid=4, EEMsgConfigSampler_sampleRate=2000, EEMsgConfigSampler_triggerLevel=0, EEMsgConfigSampler_numberOfSamplesReq=64001,  EEMsgConfigSampler_samplerReportIDType=1}"
        self.ee_write_process.stdin.write(start_sampler_cmd)
        self.ee_write_process.stdin.flush()
        return 0

    @wishful_module.bind_function(upis.mgmt.stop_energy_harvester)
    def stop_energy_harvester(self):
        self.log.info("EE Module stop_energy_harvester".format())
        self.log.info("Stop streamer".format())
        stop_sampler_cmd = "EE_MSG_CONFIG_SAMPLER{msgt_am=248, EEMsgConfigSampler_time_us=0, EEMsgConfigSampler_ADCid=4, EEMsgConfigSampler_sampleRate=2000, EEMsgConfigSampler_triggerLevel=0, EEMsgConfigSampler_numberOfSamplesReq=0,  EEMsgConfigSampler_samplerReportIDType=1}"
        self.ee_write_process.stdin.write(stop_sampler_cmd)
        self.ee_write_process.stdin.flush()
        self.log.info("Stop streamer".format())
        streamer_off_cmd = "EE_MSG_CONFIG_STREAMER{msgt_am=250, EEMsgConfigStreamer_time_us=0, EEMsgConfigStreamer_DACid=1, EEMsgConfigStreamer_sample=0, EEMsgConfigStreamer_harvesterCapacitor=0, EEMsgConfigStreamer_harvester=0, EEMsgConfigStreamer_outerLoopResistor=0, EEMsgConfigStreamer_maxDACvalue = 4095 }"
        self.ee_write_process.stdin.write(streamer_off_cmd)
        self.ee_write_process.stdin.flush()
        self.log.info("Enabling USB".format())
        enable_usb_cmd = "EE_MSG_SET_GPIO_PIN_STATUS{msgt_am=252, EEMsgSetGPIOPinStatus_time_us=0, EEMsgSetGPIOPinStatus_gpioPinStatus=0x00001800}"
        self.ee_write_process.stdin.write(enable_usb_cmd)
        self.ee_write_process.stdin.flush()
        return 0

    @wishful_module.bind_function(upis.mgmt.update_energy_harvester)
    def update_energy_harvester(self):
        self.log.info("EE Module update_energy_harvester".format())
        self.log.info("Update streamer".format())
        update_streamer_cmd = "EE_MSG_CONFIG_STREAMER{msgt_am=250, EEMsgConfigStreamer_time_us=0, EEMsgConfigStreamer_DACid=1, EEMsgConfigStreamer_sample=0, EEMsgConfigStreamer_harvesterCapacitor=500000, EEMsgConfigStreamer_harvester=10, EEMsgConfigStreamer_outerLoopResistor=0, EEMsgConfigStreamer_maxDACvalue = 4095 }"
        self.ee_write_process.stdin.write(update_streamer_cmd)
        self.ee_write_process.stdin.flush()
        return 0

    # @wishful_module.run_in_thread()
    # def before_get_rssi(self):
    #     self.log.info("This function is executed before get_rssi".format())
    #     self.stopRssi = False
    #     while not self.stopRssi:
    #         time.sleep(0.2)
    #         sample = random.randint(-90, 30)
    #         self.rssiSampleQueue.put(sample)

    #     #empty sample queue
    #     self.log.info("Empty sample queue".format())
    #     while True:
    #         try:
    #             self.rssiSampleQueue.get(block=True, timeout=0.1)
    #         except:
    #             self.log.info("Sample queue is empty".format())
    #             break

    # def after_get_rssi(self):
    #     self.log.info("This function is executed after get_rssi".format())
    #     self.stopRssi = True

    # @wishful_module.generator()
    # @wishful_module.before_call(before_get_rssi)
    # @wishful_module.after_call(after_get_rssi)
    # def get_rssi(self):
    #     self.log.debug("Get RSSI".format())
    #     while True:
    #         yield self.rssiSampleQueue.get()
