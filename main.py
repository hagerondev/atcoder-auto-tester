import os
import sys
import pathlib
import datetime
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import requests
import json
from bs4 import BeautifulSoup

DIR = (pathlib.Path(__file__).parent / "..").resolve()
FILE = "atcoder.py"
PYTHONCMD = "python"

db = (pathlib.Path(__file__).parent / "db").resolve()

class AtCoder:
	def __init__(self):
		user = os.environ['ATCODER_USERNAME']
		passwd = os.environ['ATCODER_PASSWORD']
		self.session = requests.session()
		url = "https://atcoder.jp/login"
		csrf = self.session.get(url).text.split('var csrfToken = "')[1].split('"')[0]
		r = self.session.post(url+"?continue=https%3A%2F%2Fatcoder.jp%2F",data={
			"username": user,
			"password": passwd,
			"csrf_token": csrf,
		})

	def get_input(self,path, contest, problem):
		url = f"https://atcoder.jp/contests/{contest}/tasks/{contest}_{problem}"
		res = self.session.get(url)
		# print(res)
		soup = BeautifulSoup(res.text,features="html.parser")
		sample = {"data": []}
		for div in soup.find_all(class_="part"):
			text = div.text.strip()
			if text.startswith("Sample Input "):
				s_input = div.find("pre").text
				sample["data"].append([s_input])
			elif text.startswith("Sample Output "):
				s_output = div.find("pre").text
				sample["data"][-1].append(s_output)
		with open(path, mode="w") as f:
			f.write(json.dumps(sample))

class MyHandler(PatternMatchingEventHandler):
	def __init__(self, patterns):
		super(MyHandler, self).__init__(patterns=patterns)
		self.b_data = ""
		self.ac = AtCoder()

	def get_input(self,data):
		contest = False
		problem = False
		for line in data.split("\n"):
			if line.startswith("# CONTEST: "):
				contest = line[len("# CONTEST: "):]
			elif line.startswith("# PROBLEM: "):
				problem = line[len("# PROBLEM: "):]
		if contest==False or problem==False:
			return False
		# check cash
		path = db / contest
		if not os.path.exists(str(path/problem)+".txt"):
			# download input
			os.makedirs(path, exist_ok=True)
			print(contest,problem)
			self.ac.get_input(str(path/problem)+".txt",contest,problem)

		with open(str(path/problem)+".txt",mode="r") as f:
			input_data = f.read()

		return json.loads(input_data)["data"]

	def run(self, stdins):
		for i,sample in enumerate(stdins):
			print(f"[SAMPLE {i+1}]")
			res = subprocess.run([PYTHONCMD, DIR/FILE, "DEBUG"],input=sample[0].replace("\r\n","\n"), capture_output=True, text=True)
			input_data = [">>> INPUT"]+sample[0].split("\n")
			out = [">>> YOUR OUTPUT"]
			debug = [">>> DEBUG"]
			for line in res.stdout.split("\n"):
				if line.startswith("DEBUG: "):
					debug.append(line[len("DEBUG: "):])
				else:
					out.append(line)
			cout = [">>> CORRECT OUTPUT"]+sample[1].split("\n")

			out1 = [i.rstrip() for i in sample[1].replace("\r\n","\n").rstrip().split("\n")]
			out2 = [i.rstrip() for i in "\n".join(out[1:]).rstrip().split("\n")]
			result = out1==out2

			if result:
				output = ["CORRECT!"]
			else:
				output = sample[0].split("\n")[:-1]+cout[:-1]+out[:-1]+debug
				if res.stderr!="":
					print("ERROR!")
					print(res.stderr)
			for line in output:
				if line!="\n":
					print(line)
			print()

	def on_modified(self, event):
		with open(DIR / FILE, mode="r", encoding="utf-8") as f:
			data = f.read()
		if self.b_data==data:
			return
		os.system('cls')
		print("modified",datetime.datetime.now())
		print()
		self.b_data = data
		stdin = self.get_input(data)
		if stdin==False:
			print("INVALID CONFIG")
		else:
			self.run(stdin)



if __name__ == "__main__":
	os.system('cls')
	print("START")
	print("TARGET:",FILE)
	event_handler = MyHandler([FILE])
	observer = Observer()
	observer.schedule(event_handler, DIR, recursive=True)
	observer.start()
	try:
		while True:
			time.sleep(1)
	except KeyboardInterrupt:
		observer.stop()
	observer.join()