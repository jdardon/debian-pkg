#
# Regular cron jobs for the editobj2 package
#
0 4	* * *	root	[ -x /usr/bin/editobj2_maintenance ] && /usr/bin/editobj2_maintenance
