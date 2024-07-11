class ztmUserInput:    
    def adcStartMsg():
        calStartMsg = ("---------------------------------------------\n" +
               "Electron Tunneling Microscope ADC Calibration\n" +
               "---------------------------------------------\n")   
        print(calStartMsg)

        calNextMsg = ("For this procedure, you will need to have the Electron Tunneling Miscroscope (ZTM)\n"  +
              "powered on and connected to the PC with a USB cable. The Pre-Amplifier PCB\n"          +
              "(located on the microscope) should have the wire to the tip disconnected - that is,\n" +
              "the wire that is normally connected to the middle terminal labeled ""Tunnel Sig"".\n\n")
        print(calNextMsg)
    
    def getComPort():
        stmCOM = input ("Please enter the COM Port to which the Electron Microscope is connected.\n"+
                        "To do this:\n"+
                        "> Open the 'Device Manager'\n"+
                        "> Go down to 'Ports'\n"+
                        "> Find the COM Port that the Electron Miscroscope is connected to.\n"             +
                        "> Enter only the COM number\n\te.g if the ZTM Controller is connected to COM8,\n\t" +
                        "enter the number 8 and then press <enter>.\n" +
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
              "---------------------------------------------\n"
              "> Make sure the Bias and Piezo terminals on the Pre-Amplifier PCB are disconnected\n" +
              "> Connect a short wire from the 'GROUND' terminal of the 'Tunnel Sig' terminal block to\n" +
              "  the 'TUN' terminal. This will ground the input of the Pre-Amplifier circuit.\n"+
              "> When you have connected the wire and tightened the terminal screws, place the enclosure\n"+
              "  cover over the microscope to shield to Pre-Amplifier from any electromagnetic interference (EMI)\n")
        print(calMsg) 