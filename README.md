## Generate Python protocol class
python slpdgen-py/src/main.py py-proto proto.slpd

## Generate Wireshark dissector
python slpdgen-py/src/main.py dissector ICP.slpd --port 9800

## Show all available commands
python slpdgen-py/src/main.py --help
