import praw
import sqlite3
import time


def get_row_exists(table, column, value):
	c.execute("SELECT count(*) FROM "+table+" WHERE "+column+"=? COLLATE NOCASE", (value,))
	data = c.fetchone()[0]
	if data==0:
		return False
	else:
		return True


def gen_log(data):
	f = open(LOGFILE, 'a')
	datetime =  str(time.strftime("%Y/%m/%d")) + " " + str(time.strftime("%H:%M:%S"))
	f.write(datetime + ": " + data + "\n")
	f.close()
	print datetime + ": " + data


### MAIN #############################################
r = praw.Reddit("/r/rainmeter source enforcer by /u/Pandemic21")
USERNAME=''
PASSWORD=''
LOGFILE='/home/pandemic/Documents/scripts/rainmeter/rainmeter.log'
GRACE_PERIOD=60*60*6 # 6 hours in seconds	
COMMENT_TEXT="It looks like your submission does not comply with Rule B.1.\n\n>If you share a completed setup, provide download links to skins and wallpapers shown within six hours of posting.\n\nPlease reply to your submission with the download links."
sub = r.get_subreddit("rainmeter")
conn = sqlite3.connect('/home/pandemic/Documents/scripts/rainmeter/rainmeter.db')
c = conn.cursor()

c.execute("CREATE TABLE IF NOT EXISTS submissions (id text, time text)")
conn.commit()
r.login(USERNAME,PASSWORD,disable_warning=True)

while 1:
	#search for new submissions
	posts = sub.get_new(limit=10)
	for post in posts:
		if post.is_self:
			gen_log(post.id + " is a self-post")
			continue
		if get_row_exists("submissions", "id", post.id):
			gen_log(post.id + " has already been added")
			continue
		gen_log("Adding " + post.id)
		c.execute("INSERT INTO submissions VALUES (?, ?)", (post.id, str(post.created_utc + GRACE_PERIOD)))
		conn.commit()

	#check old submissions
	t = time.time()
	c.execute("SELECT * FROM submissions")
	rows = c.fetchall()

	for row in rows:
		if float(row[1]) > t:
			gen_log(row[0] + " has " + str(float(row[1])-t) + " seconds left")
			continue

		gen_log("Checking " + row[0] + "...")
		c.execute("DELETE FROM submissions WHERE id=?", (row[0],))
		conn.commit()

		op_has_replied = False
		s = r.get_submission(submission_id=row[0])
		op = str(s.author)
		comments = s.comments

		for comment in comments:
			if op == str(comment.author):
				gen_log("OP replied, comment.id = " + comment.id)
				op_has_replied = True
		if op_has_replied:
			continue
		gen_log("OP hasn't replied, adding comment")
		s.add_comment(COMMENT_TEXT)

	time.sleep(60*5)
