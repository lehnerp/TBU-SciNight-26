# Old Prototypes – Archived Reference

These earlier standalone Arduino sketches are no longer used in the current
setup. They are preserved as historical references and are not part of the
active projects or their installation process.

| Prototype | Original purpose | Current project |
| --- | --- | --- |
| [Display_I2C_Keypad](Display_I2C_Keypad/Display_I2C_Keypad.ino) | LCD/keypad access check with PIN `1234` and key `TESTER`. | [PIN and LED Rings](../PIN_Klavesnice/README.md) |
| [NFC_Simple_Driver_Smiley](NFC_Simple_Driver_Smiley/NFC_Simple_Driver_Smiley.ino) | RC522 card check with a smiley on a MAX7219 matrix. | [NFC Sequence](../NFC_Sekvence/README.md) |
| [NFC_Simple_Driver_Tick](NFC_Simple_Driver_Tick/NFC_Simple_Driver_Tick.ino) | RC522 card check with a check mark on a MAX7219 matrix. | [NFC Sequence](../NFC_Sekvence/README.md) |

The NFC prototypes use allowed UID `A0:5E:E1:28`. These standalone versions
do not implement the serial protocols used by the current Python drivers.
Refer to the active projects for current dependencies, wiring, and setup.

[Project overview](../README.md).
