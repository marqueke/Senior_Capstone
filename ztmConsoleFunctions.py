

class ztmUserInput: 

    def adcStartMsg():
        calStartMsg = ( "---------------------------------------------\n" +
                        "Electron Tunneling Microscope ADC Calibration\n" +
                        "---------------------------------------------\n")   
        print(calStartMsg)

        calNextMsg = ("For this procedure, you will need to have the Electron Tunneling Miscroscope (ZTM)\n"  +
              "powered on and connected to the PC with a USB cable. The Pre-Amplifier PCB\n"          +
              "(located on the microscope) should have the wire to the tip disconnected - that is,\n" +
              "the wire that is normally connected to the middle terminal labeled ""Tunnel Sig"".\n\n")
        print(calNextMsg)

    def dacStartMsg():
        calStartMsg = ( "---------------------------------------------\n" +
                        "Electron Tunneling Microscope DAC Calibration\n" +
                        "---------------------------------------------\n")   
        print(calStartMsg)

        calNextMsg = (  "For this procedure, you will need to have the Electron Tunneling Miscroscope (ZTM)\n"  +
                        "powered on and connected to the PC with a USB cable. The Pre-Amplifier PCB\n"          +
                        "(located on the microscope) should have the wires to the sample and the piezo actuator\n"+
                        "disconnected. These are normally connected in the terminal blocks labeled 'SAMPLE' and\n"+
                        "'PIEZO'. You will need a small, flathead screwdriver to disconnect them.\n"+
                        "In addition, this procedure requires a precision DMM (digital multimeter) and test probes.\n"+
                        "The DMM should be set to measure voltage with the highest degree of precision available.\n"+
                        "---------------------------------------------\n\n")
        print(calNextMsg)

    def getComPort():
        stmCOM = input ("Please enter the COM Port to which the Electron Microscope is connected.\n"+
                        "To do this:\n"+
                        "> Open the 'Device Manager'\n"+
                        "> Go down to 'Ports'\n"+
                        "> Find the COM Port that the Electron Miscroscope is connected to.\n"             +
                        "> Enter only the COM number\n"+
                        "\te.g if the ZTM Controller is connected to COM8,\n" +
                        "\tenter the number 8 and then press <enter>.\n" +
                        "> COM Port: ") 
        print("\n")
        return stmCOM   

    def checkComEntry(entry):
        if(entry.isnumeric()):
            return 1
        else:
            print ("> Please enter ONLY the COM Port number, i.e. 1, 3, 15, etc., then \n"+
                   "  press <enter>\n\n")
            return 0

    def confirmEntry(entry):                
        print("You entered " + entry + ", is this correct?\n")
        verify = input ("\t> Enter <Y> for yes\n" +
                        "\t> Enter <N> for no, then press <enter> ")
        print("\n")    
        if(verify == "y" or verify == "Y"):       
            return 1
        else:
            return 0

    def getNewEntry():
        stmCOM = input ("> Enter COM port: ")
        print("\n")
        return stmCOM
    
    def adcCalGetTestCurrent():

        calMsg = ("INPUT TEST CURRENT VALUE\n" + 
              "---------------------------------------------\n"+
              "The Pre-Amplifier PCB has an on-board Test Current circuit\n" +
              "to be used for calibration. This current varies due to the\n" +
              "tolerance of the resistors and is different for each PCB. Your\n"+
              "Pre-Amplifier should have a label that denotes the Test Current in\n"+
              "nano-Amps.\n\n")
        print(calMsg) 


    def adcCal0Vmsg():
        calMsg = ("0V OFFSET CALIBRATION\n" +
              "---------------------------------------------\n"+
              "> Make sure the 'TUNNEL', 'SAMPLE' and 'PIEZO' terminals on the Pre-Amplifier PCB have all wires disconnected.\n" +
              "> Connect a large resistor from the 'SIG' port of the 'TUNNEL' terminal block to ground for the 0V offset.\n"+
              " \tThe resistor should be at least 1-10 MegaOhms."
              "> Place the enclosure cover over the microscope to shield to Pre-Amplifier from any electromagnetic interference (EMI)\n\n")
        print(calMsg) 

    def adcCalTestCurrMsg():
        calMsg = ("GAIN CALIBRATION\n" +
              "---------------------------------------------\n"+
              "> Remove the cover from over the microscope.\n"+
              "> Disconnect the Pre-Amplifier from the Ethernet cable.\n"+
              "> Locate the female header socket labelled 'TEST CURR' on the Pre-Amplifier.\n" +
              "> Connect a short jumper wire from the 'TEST CURR' socket to the 'SIG' terminal.\n"+
              "> Make sure the 'SIG' terminal screw is securely tightened.\n"+
              "> When you have connected the wire and tightened the terminal screws:\n"+
              "\t> Reconnect the Ethernet cable\n"+
              "\t> Place the enclosure cover over the microscope to shield to Pre-Amplifier from any electromagnetic interference (EMI)\n\n")
        print(calMsg)      

    def dacCalSelectChannel():
        dacSel = input ("---------------------------------------------\n"+
                        "> First, select which DAC channel to calibrate. Enter <bias> or <piezo>, then press <enter>\n"
                        "> Channel Selected: ")
        return(dacSel)        

    def dacCalSetup(dacSel, termLabel):
            
        calMsg = ("    Set Up\n"+
                  "--------------\n"+
                  "> Turn on the DMM and plug in the test probes. \n"+
                  f"\t>The cleanest measurement will be made if the DMM's test probes can be screwed directly into the {dacSel} terminals,\n".format(dacSel) +
                   "\t but measurements taken with the test probes held on the terminals should be sufficient.\n"+
                  "> The common (Ground) probe should go to the terminal labeled 'GND'\n"+
                  f"> The positive probe should go to the terminal labeled '{termLabel}'.\n\n".format(termLabel))
        print(calMsg)
    
    def dacCalUserEntry(dacSel, termLabel):

        calMsg = ("Please enter the DMM's average voltage reading in the console, then press <enter>\n") 

        print(calMsg)   

           