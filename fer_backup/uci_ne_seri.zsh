#!/bin/zsh

# The dynamic ASCII art text

message="██╗   ██╗ ██████╗██╗    ██╗    ███╗   ██╗███████╗    ███████╗███████╗██████╗ ██╗██╗
██║   ██║██╔════╝██║    ██║    ████╗  ██║██╔════╝    ██╔════╝██╔════╝██╔══██╗██║██║
██║   ██║██║     ██║    ██║    ██╔██╗ ██║█████╗      ███████╗█████╗  ██████╔╝██║██║
██║   ██║██║     ██║    ██║    ██║╚██╗██║██╔══╝      ╚════██║██╔══╝  ██╔══██╗██║╚═╝
╚██████╔╝╚██████╗██║    ██║    ██║ ╚████║███████╗    ███████║███████╗██║  ██║██║██╗
 ╚═════╝  ╚═════╝╚═╝    ╚═╝    ╚═╝  ╚═══╝╚══════╝    ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝"

# Define an array of colors for the dynamic left part
colors=(
    '\033[31m' # Red
    '\033[32m' # Green
    '\033[33m' # Yellow
    '\033[34m' # Blue
    '\033[35m' # Magenta
    '\033[36m' # Cyan
    '\033[37m' # White
)

# Fixed color for the right part
right_color='\033[37m' # White

while true; do
    for color in "${colors[@]}"; do
        echo -e "${christmas_hat}"
        echo -e "${color}${message}${tree}\033[0m"

        # Pause for a short time and clear the screen
        sleep 0.2
        clear
    done
done
