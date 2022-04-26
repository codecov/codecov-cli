import os
import shutil
import subprocess


from glob import glob
from pathlib import Path


class Pycoverage(object):
    def run_preparation(self, collector):        
        print("Running coverage.py plugin...")
        
        if shutil.which("coverage") is None:
            print("coverage.py is not installed or can't be found.")
            print("aborting coverage.py plugin...")
            return
        
        
        successfully_generated = self._generate_XML_report(os.getcwd())
        
        
        if successfully_generated:
            print("aborting coverage.py plugin...")
            return
            
        
        print(f"Couldn't find coverage data in {os.getcwd()}. Searching in subdirectories...")
        
        
        # This might need optimization
        coverage_data = glob("**/.coverage", recursive=True) or glob("**/.coverage.*", recursive=True) 
        
        
        if not coverage_data:
            print("No coverage data found.")
            print("aborting coverage.py plugin...")
            return

        
        coverage_data_directory = os.path.join(os.getcwd(), Path(coverage_data[0]).parent) # absolute paths are more clear for the user
        self._generate_XML_report(coverage_data_directory)
        
        print("aborting coverage.py plugin...")
           
        
        
        
    def _generate_XML_report(self, dir):
        '''Generates up-to-date XML report in the given directory, returns true if successfully generated'''
        
        # the following if conditions avoid creating dummy .coverage file
        
        if glob(os.path.join(dir, ".coverage.*")):
            print(f"Running coverage combine -a in {dir}")
            subprocess.run(["coverage", "combine", "-a"], cwd=dir)
        
        
        if os.path.exists(os.path.join(dir, ".coverage")):
            print(f"Generating coverage.xml report in {dir}")
            completed_process = subprocess.run(["coverage", "xml", "-i"], cwd=dir, capture_output=True)
            
            output = completed_process.stdout.decode().strip()
            print(output)
            
            return output == "Wrote XML report to coverage.xml"


        return False
            
            
        
        
