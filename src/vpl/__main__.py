# main file


import sys

def print_info():
    print ("error, need to use a sub program:")
    print ("")
    print ("  python3 -mvpl webcam       webcam viewer")
    print ("  python3 -mvpl video        video processor")
    print ("")
    print ("use these subcommands' --help option to view more info")

if len(sys.argv) <= 1:
    print_info()
    exit(1)
else:
    subp = sys.argv[1]
    sys.argv = [sys.argv[0]] + sys.argv[2:]
    if subp == "webcam":
        from vpl.examples import webcam
    elif subp == "video":
        from vpl.examples import video
    else:
        print_info()
        exit(1)
