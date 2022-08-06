import os
import sys
import time
import json
import requests
import pathlib
import datetime
import subprocess
from bs4 import BeautifulSoup
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

DIR = (pathlib.Path(__file__).parent / "..").resolve()
FILE = "atcoder.py"
PYTHONCMD = "python"

db = (pathlib.Path(__file__).parent / "db").resolve()

class AtCoder:
	def __init__(self):
		# atcoder login
		url = "https://atcoder.jp/login"
		user = os.environ['ATCODER_USERNAME']
		passwd = os.environ['ATCODER_PASSWORD']
		self.session = requests.session()
		csrf = self.session.get(url).text.split('var csrfToken = "')[1].split('"')[0]
		r = self.session.post(url+"?continue=https%3A%2F%2Fatcoder.jp%2F",data={
			"username": user,
			"password": passwd,
			"csrf_token": csrf,
		})

	def get_input(self,path, contest, problem):
		# problem url
		url = f"https://atcoder.jp/contests/{contest}/tasks/{contest}_{problem}"
		soup = BeautifulSoup(self.session.get(url).text,features="html.parser")
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

		path = db / contest
		# check cash
		if not os.path.exists(str(path/problem)+".txt"):
			# download input
			os.makedirs(path, exist_ok=True)
			self.ac.get_input(str(path/problem)+".txt",contest,problem)

		with open(str(path/problem)+".txt",mode="r") as f:
			input_data = f.read()

		return json.loads(input_data)["data"]

	def run(self, stdins):
		for i,sample in enumerate(stdins):
			res = subprocess.run([PYTHONCMD, DIR/FILE, "DEBUG"],input=sample[0].replace("\r\n","\n"), capture_output=True, text=True)
			# input
			print(f"[SAMPLE {i+1}]")
			input_data = [">>> INPUT"]+sample[0].split("\n")
			out_y,out_d = [">>> YOUR OUTPUT"],[">>> DEBUG"]
			for line in res.stdout.split("\n"):
				if line.startswith("DEBUG: "):
					out_d.append(line[len("DEBUG: "):])
				else:
					out_y.append(line)
			out_c = [">>> CORRECT OUTPUT"]+sample[1].split("\n")

			out1 = [i.rstrip() for i in sample[1].replace("\r\n","\n").rstrip().split("\n")]
			out2 = [i.rstrip() for i in "\n".join(out_y[1:]).rstrip().split("\n")]
			result = out1==out2

			if result:
				output = "CORRECT!"
			else:
				output = [
					"\n".join(input_data).rstrip(),
					"\n".join(out_c).rstrip(),
					"\n".join(out_y).rstrip(),
					"\n".join(out_d).rstrip(),
				]
				output = "\n".join(output)
				if res.stderr!="":
					print("ERROR!")
					print(res.stderr)
			print(output+"\n")

	def on_modified(self, event):
		with open(DIR / FILE, mode="r", encoding="utf-8") as f:
			data = f.read()
		# fileが更新されているか
		if self.b_data==data:
			return
		self.b_data = data
		os.system('cls')
		print("modified",datetime.datetime.now())
		print()
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