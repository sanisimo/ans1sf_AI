**This is a converted version of the original file 'instructions2.pdf'.**

# **Task2: Technical Task with pytest**

**Objective:** Fix the get_uptime_seconds method in the provided driver and write a pytest suite to verify its
functionality according to the included specification.


   - **Provided Files:** instructions.pdf (this document), uhf_driver.py

   - **Deliverables:** A single .zip archive containing the modified uhf_driver.py and the
new test_uhf_driver.py.

   - **Estimated Time:** 2-3 hours.


You are a System Test Engineer at EnduroSat. You have been given a preliminary Python driver
(uhf_driver.py) for our UHF radio and the official protocol documentation for the "Read Uptime" command.


During review, it was discovered that the get_uptime_seconds() method in the driver is outdated and does
not match the current protocol specification.


**Protocol Specification for Uptime:**


   - **Command:** ES+R[AA]02...

   - **Response:** OK+[RR][PPPPPPPP][B][C..C]

   - [PPPPPPPP] is the uptime value in seconds, represented as an **8-character HEX string** .

   - [RR] is the 2-character RSSI value, which precedes the uptime data.

   - **Example Response:** OK+D8001A2B3C DEADBEEF where D8 is the RSSI and 001A2B3C is the
uptime.


**Your Task (Two Parts):**


**Part 1: Fix the Driver**


1. Based on the specification above, modify the get_uptime_seconds() method inside uhf_driver.py so
that it sends the correct command and correctly parses the specified response to return the uptime
as an **integer** number of seconds.
2. You must also update the MockSerial class to respond correctly to the new command.


**Part 2: Write the Tests**


1. In a new file, test_uhf_driver.py, write a suite of pytest tests to prove your fix is correct and the driver

is robust.

2. Your test suite must include, at a minimum:

        - A test for the successful parsing of the uptime value.

        - A test proving the driver raises an error if the hardware returns a malformed or corrupted

response.

       - A test for the get_status_control_word() method to ensure it was not broken by your
changes.


**A Note on pytest:** _If you are new to pytest, don't worry. We are interested in your testing logic and problem-_
_solving approach, not your memorization of syntax. The official pytest documentation is a great resource._


**Status Control Word (SCW) [Application / Bootloader]**


SCW format:

|15|14|13|12|11|10|9|8|7|6|5|4|3|2|1|0|
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|**Reserved**|**Reserved**|**UartBaud**|**UartBaud**|**Reset**|**RfMode**|**RfMode**|**RfMode**|**Echo**|**BCN**|**Pipe**|**Boot**|**CTS**|**SEC**|**FRAM**|**RFTS**|
|0|0|r/w-3|r/w-3|r/w-0|r/w-3|r/w-3|r/w-3|r/w-0|r/w-0|r/w-0|r-X|r-X|r-X|r-X|r-X|


|Bitfield|Meaning|
|---|---|
|[15]|**Reserved:** For future use (default value is 0)|
|[14]|**HFXT:**High frequency oscillator status, 0– oscillator OK, 1– oscillator error|
|[13, 12]|**UartBaud:** Speed of the UART interface. Possible values 00-9600, 01 - reserved, 10-<br>19200, 11-115200 (default).<br>**NOTE:** 230.400 kbps UART interface speed supported (optional)|
|[11]|**Reset:** Write 1 to reset the device, 0– no effect (default)|
|[10, 9,8]|**RFMode:** see Table 9|
|[7]|**Echo**: Local UART echo of the transmitted symbols over the radio when a valid ESTTC<br>command is received via radio; 1– Echo on, 0– Echo off (default)|
|[6]|**BCN**: Beacon message control; 1– enabled, 0– disabled (default)|
|[5]|**Pipe**: Transparent mode communication control; 1 – Pipe mode on, 0 – Pipe mode off<br>(default)|
|[4]|**Boot**: Indicates whether the device is in bootloader or application mode<br>1 – Bootloader, 0– Application|
|[3]|**CTS**: Reserved for future use (default value is 0)|
|[2]|**SEC**: Reserved (default value is 0)|
|[1]|**FRAM**: Indicates whether FRAM is initialized correctly after reset; 1 – OK, 0 – FRAM<br>Error|
|[0]|**RFTS**: Indicates whether radio transceiver is initialized correctly after reset; 1 – OK,<br>0 – Radio Error|



To switch back and forth between bootloader and application the user will have to set both **Bit 4** and
**Bit 11** bearing in mind their effect as described in the above table. If only **Bit 4** is set/cleared the
device will stay in its current mode (bootloader or application).

|RFMode#|Modulation|Datarate [bps]<br>,|Fdev [Hz]<br>,|ModInd|
|---|---|---|---|---|
|0 [000]|2GFSK|1200|600|1|
|1 [001]|2GFSK|2400|600|0.5|
|2 [010]|2GFSK|4800|1200|0.5|
|**3 [011] (default)**|**2GFSK**|**9600**|**2400**|**0.5**|
|4 [100]|2GFSK|9600|4800|1|
|5 [101]|2GFSK|19200|4800|0.5|
|6 [110]|2GFSK|19200|9600|1|
|7 [111]|2GFSK|19200|19200|2|



Table 11: Available RF modes


**NOTE:** For other modulations schemes please contact EnduroSat for support. Up to 16 different RF
modes (modulation, data rate, frequency deviation) can be preconfigured with one more bit
(optional).


**Status Control Word**


|Write|Answer|
|---|---|
|ES+W[AA]00[WWWW][B][C..C]<CR>|1)<br>OK+[WWWW][B][C..C]<CR><br>:<br>successful<br>configuration<br>2) +ESTTC[B][C..C]<CR>: response at exit of PIPE mode<br>(not valid if command is sent via I2C)|
|**Read**|**Answer**|
|ES+R[AA]00[B][C..C]<CR>|OK+[RR][AA][BB][WWWW][B][C..C]<CR>|



**[AA]** is the device address in HEX format;

**[WWWW]** is a 16-bit value in HEX format use to modify the SCW bit fields in “Write” command
and current SCW content as a result of “Write” and “Read” command execution;

**[RR]** is the last received signal strength indicator (RSSI);

**[BB]** is the reset counter. It counts times device has undergone reset (power down, reset via
command, new SW via bootloader);

**[B]** is the blank space ASCII character;

**[C..C]** are the 8 ASCII characters representing the calculated CRC32;
**Example commands:**

    - ES+R2200 BD888E1F<CR>

    - ES+W22003323 589B0F83<CR>

|Read Uptime [Application / Bootloader]|Col2|
|---|---|
|**Uptime**|**Uptime**|
|**Read**|**Answer**|
|ES+R[AA]02[B][C..C]<CR>|OK+[RR][PPPPPPPP][B][C..C]<CR>|



**[AA]** is the device address in HEX format;

**[PPPPPPPP]** is the uptime value in seconds in HEX format;

**[RR]** is the last RSSI;

**[B]** is the blank space ASCII character;

**[C..C]** are the 8 ASCII characters representing the calculated CRC32;
**Example commands:**

    - ES+R2202 5386EF33<CR>


