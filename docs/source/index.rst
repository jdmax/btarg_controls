.. Hall B Cryotarget Control documentation master file, created by
   sphinx-quickstart on Fri Aug 18 10:04:29 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Hall B Cryotarget Control's documentation!
=====================================================

The new Hall B Cryotarget Controls provide an interface between the target instruments, valves and heaters using Python SoftIOCs for EPICS. All the devices that control the target are network enabled, and each device has its own stand-alone SoftIOC to create and set Process Variables which can be set and read from the EPICS network. Any SoftIOC needs only a Telnet connection to its device, so it could be run on any computer on the same network. Each SoftIOC is run via the :class:`Master IOC <master_ioc>` Python script, which accepts a command argument to determine which IOC to start.

Because there are many instruments, and thus many control IOCs, I've written an :class:`IOC Manager <ioc_manager>`, which creates Process Variables to start, stop or reset each or all IOCs. The IOCs and their settings are listed in a :doc:`settings` 'settings.yaml'. This file also determines which IOCs are listed for use in the IOC Manager, and defines process variable names for each channel on a device.

The frontend graphical user interface is written in Phoebus CSS. The frontend is independent from the backend device IOCs, and only provides a means for a user to get and set the Process Variables of all the IOCs through EPICS.

IOC Manager
===========
The IOC manager is the main script a user will interact with to start the backend software. The :class:`IOC Manager <ioc_manager>` must be run from the command line as ``python ioc_manger.py``. Once run, it enters into a interactive mode that has a few commands to see the PVs, but most interaction with it should be done through its EPICS variables.  The IOC has multiple choice PVs for each device listed in the 'settings.yaml' file, allowing the setting of a PV to perform that action. For instance, a PV ``ami136_control`` will be created with the options Start, Stop, Reset and Kill.

To start a device IOC, the :class:`IOC Manager Class <ioc_manager.IOCManager>` first opens a  :class:`Start Thread <ioc_manager.StartThread>`. This thread then opens an instance of Unix screen named after the device, in which the Master IOC is run for the given device. Once the Master IOC is run, the manager waits for it to start, then reads out all the PVs from that IOC. The Screens created on the computer can be listed with ``screen -ls``, and any Screen can be entered with ``screen -r [name]`` to see messages from that IOC.

An **all** PV is also created, which will perform the selected action for all the devices with autostart set to True in the settings.yaml file.

Master IOC
==========
The :class:`Master IOC <master_ioc>` sets up an IOC to interact with a single device. It first :class:`loads settings <master_ioc.load_settings>`, reading the settings.yaml file. If a device from the file is given on the command line, as in ``python master_ioc.py -i lakeshore_336``, the master IOC will use the module code from that entry in the settings file to run the IOC. If no ``-i`` argument is given, it will list the options from the settings file.

The main class in the master IOC is :class:`DeviceIOC <master_ioc.DeviceIOC>`, which creates an instance of the device using the module chosen and starts the loop to run it.

Device IOCs
===========

The device IOC modules contain the specific code to interact with a given device, and code is separated into two classes. The device class, :class:`AMI136 level controller <devices.ami136.Device>` for instance, is standardized so that all the modules provide the methods for the master IOC, such as , :class:`connect <devices.ami136.Device.connect>`, :class:`do_reads <devices.ami136.Device.do_reads>`, :class:`do_sets <devices.ami136.Device.do_sets>`, and :class:`set alarm <devices.ami136.Device.set_alarm>`. The standardized methods are then connected to the specific functions for each device in the connection class.  The :class:`Device Connection <devices.ami136.DeviceConnection>` contains the Telnet connection and specific methods to read and control the device, such as :class:`read <devices.ami136.DeviceConnection.read>`.

Settings Files
==============
The majority of the required settings for each device are in the :doc:`settings` ``settings.yaml``. Each top level entry defines a device which needs an IOC, and it has subentries to give the connection addresses, read delay and timeout. A ``channels`` entry lists ll the channels for that device in order; for instance the 8 channels of a Lakeshore 218 temperature monitor are listed as names in their order on the device.  In general, each channel defines a Process variable with a corresponding suffix, such as a temperature indicator ``Shield_Cold_TI``. Some channels do not include a suffix, in which case their modules create multiple PVs based on that channel name.


The records.yaml file defines default fields for PVs created from the settings.yaml file. All entries in the records file are optional, but allow descriptions, units and starting alarm values to be defined.

Status Changes
==============
The :class:`Status IOC <devices.status_ioc>` facilitates the switching of the target state, for instance from cooling down to filling. The status has two multiple choice PVs, ``species`` and ``status``. If either are changed, the IOC will update all the process variables listed in the :doc:`states` ``states.yaml``, performing EPICS puts on each. The states file is organized by state, i.e Cooldown, Empty, Full or Safe. Each entry is a PV to be updated for that state, and each PV has a list of the values for each species. Values that are lists are taken as alarm limits (HIHI, HIGH, LOW, LOLO). The status IOC can be started like any other device IOC using the IOC manager.


Software PIDS
=============
The :class:`PID IOC <pids>` PID IOC allows software PID control of any EPICS PV using any other PV. The code looks at the :doc:`pids_file` ``pids.yaml`` and creates a new PID coroutine to perform gets and puts to control a PID loop. Any number of PIDs may be created, just restart the PID IOC after changes to the file. The PID IOC can also be controlled from the IOC Manager with its own PV.


.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
