# elt-encoder
Python utility to encode - decode ELT messages

Code is part of bigger project found on GitHub :
https://github.com/jrreich/MEO_Analysis_HTML_Interface
 
Full credits to its author - I have just repackaged it for some tests.

## Usage 
### From the terminal line
Check the details from the command line.
By default only Standard Location protocol with long message and MMSI id is directly supported.  

### Example as a module

    frame = 'test'
    protocol = 'standard'
    serial = 1
    latitude = None
    longitude = None
    homing = 0
    country = 'Belgium'
    
    digital_msg = DigitalMessage( frame, protocol)
    digital_msg.message.country = country
    digital_msg.message.serialid = serial
    digital_msg.message.latitude = latitude
    digital_msg.message.longitude = longitude
    digital_msg.message.has_homing = str(homing)
    
    print(digital_msg.bitstring)
    digital_msg.update()
    print(len(digital_msg), len(digital_msg.message.pdf1),  len(digital_msg.message.pdf2))
    print(digital_msg.message.pdf1.data)
    print(digital_msg.message.pdf1.bch)
    print(digital_msg.message.pdf2.data)
    print(digital_msg.message.pdf2.bch)
    