import cv2
import win32api
import win32con
import win32gui

# Get the number of display monitors
num_monitors = win32api.GetSystemMetrics(win32con.SM_CMONITORS)

# Loop through each display monitor
for i in range(num_monitors):
    # Get the monitor handle and info
    monitor_handle = win32api.EnumDisplayMonitors(None, None)[i][0]
    monitor_info = win32api.GetMonitorInfo(monitor_handle)
    
    # Get the resolution, x and y location, and alignment of the monitor
    x_resolution = monitor_info[2][0]
    y_resolution = monitor_info[2][1]
    x = monitor_info[0][0]
    y = monitor_info[0][1]
    alignment = monitor_info[1]
    
    # Create a rectangular mapping for the monitor
    rect = ((x, y), (x + x_resolution, y + y_resolution))
    
    # Add text with a rectangular if the monitor is the primary monitor
    if alignment == win32con.MONITORINFOF_PRIMARY:
        img = cv2.rectangle(img, rect[0], rect[1], (0, 255, 0), 2)
        img = cv2.putText(img, "Primary Monitor", (rect[0][0] + 10, rect[0][1] + 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
    else:
        img = cv2.rectangle(img, rect[0], rect[1], (255, 0, 0), 2)
    
# Show the image
cv2.imshow("Monitor Mapping", img)
cv2.waitKey(0)
cv2.destroyAllWindows()
