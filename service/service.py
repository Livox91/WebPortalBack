import win32service
import win32serviceutil
import win32event
import subprocess
import os

class DualWebServerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "DualWebServerService"
    _svc_display_name_ = "Dual Web Server Service"
    _svc_description_ = "A service that starts Flask and Angular servers"

    def __init__(self, args):
        super().__init__(args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.flask_process = None
        self.angular_process = None
        self.log_file = r"C:\service_log.txt"  # Change this to a valid path

    def log(self, message):
        """Log messages for debugging."""
        with open(self.log_file, "a") as f:
            f.write(message + "\n")

    def start_servers(self):
        """Start Flask and Angular servers."""
        flask_env_path = r"C:\Users\HP\Documents\Projects\HasanHaider\Back\myvenv\Scripts\python.exe"  # Virtual environment Python
        flask_app_path = r"C:\Users\HP\Documents\Projects\HasanHaider\Back\server.py"  # Flask app
        angular_project_path = r"C:\Users\HP\Documents\Projects\HasanHaider\Front\Hasan"  # Angular project folder
        npm_path = r"C:\Program Files\nodejs\npm.cmd"  # npm path
          
        self.log("Starting Flask and Angular servers...")

        try:
            # Start Flask with virtual environment
            self.flask_process = subprocess.Popen(
                [flask_env_path, flask_app_path], 
                cwd=os.path.dirname(flask_app_path),
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS
            )
            self.log("Flask server started.")

            # Start Angular using npx ng serve
            self.angular_process = subprocess.Popen(
                [npm_path,"run" ,"start"],   
                cwd=angular_project_path,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=subprocess.DETACHED_PROCESS
            )
            self.log("Angular server started.")

        except Exception as e:
            self.log(f"Error starting servers: {str(e)}")

    def SvcStop(self):
        """Stop the service and terminate both servers."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        if self.flask_process:
            self.flask_process.terminate()
        if self.angular_process:
            self.angular_process.terminate()
        win32event.SetEvent(self.stop_event)
        self.log("Service stopped.")

    def SvcDoRun(self):
        """Main function that runs the servers."""
        self.start_servers()
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(DualWebServerService)
