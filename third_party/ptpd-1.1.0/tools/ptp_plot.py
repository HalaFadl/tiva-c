#! /usr/bin/env python2.6
# Copyright (c) 2010, Neville-Neil Consulting
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# Neither the name of Neville-Neil Consulting nor the names of its 
# contributors may be used to endorse or promote products derived from 
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: George V. Neville-Neil
#
# Description: 

"""ptp_plot.py -- Plot PTP delays reported by the slave.

This program takes a ptp log file generated by the slave
and plots various times on a graph

This program requires at least python2.6 as well as numpy
and gnuplot support.

"""

import csv
import datetime
import subprocess
import sys
import tempfile

from numpy import *

import Gnuplot, Gnuplot.funcutils

def usage():
    sys.exit()

def main():

    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-a", "--all", dest="all", default=0,
                      help="show all entries")
    parser.add_option("-t", "--type", dest="type", default="delay",
                      help="plot the delay or offset")
    parser.add_option("-l", "--logfile", dest="logfile", default=None,
                      help="logfile to use")
    parser.add_option("-s", "--start", dest="start", default="09:30:00",
                      help="start time")
    parser.add_option("-e", "--end", dest="end", default="16:30:00",
                      help="end time")
    parser.add_option("-r", "--roll", dest="roll", type=int, default=0,
                      help="number of days to roll at the start")
    parser.add_option("-p", "--print", dest="png", default=None,
                      help="file to print the graph to")
    parser.add_option("-y", "--ymin", dest="ymin", default="0.000000",
                      help="minimum y value")
    parser.add_option("-Y", "--ymax", dest="ymax", default="0.001000",
                      help="maximum y value")
    parser.add_option("-S", "--save", dest="save", default=None,
                      help="save file name")


    (options, args) = parser.parse_args()
    
    if ((options.type != "delay") and (options.type != "offset")):
        print "You must choose either delay or offset."
        usage()

    try:
        logfile = csv.reader(open(options.logfile, "rb"))
    except:
        print "Could not open %s" % options.logfile
        sys.exit()
        
    #
    # This is an ugly hack, but it turns out that gnuplot
    # is better able to plot time data if we write it out
    # in the familiar format to a temporary file and
    # then plot from the file rather than building up
    # arrays of data.
    #
    tmpfile = tempfile.NamedTemporaryFile()

    savefile = None
    
    if (options.save != None):
        savefile = open(options.save, "w")
    

    first = True
    for line in logfile:
        # Split off the microseconds
        try: 
            dt = line[0].rpartition(':')[0]
        except:
            continue
        now = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
        if (first == True):
            if (options.all == 0):
                start = datetime.datetime.strptime(options.start, "%H:%M:%S")
            else:
                start = now
            start = start.replace(year=now.year, month=now.month,
                                  day=now.day + options.roll)
            end = datetime.datetime.strptime(options.end, "%H:%M:%S")
            end = end.replace(year=now.year, month=now.month,
                              day=now.day + options.roll)
            first = False
        if ((now > end) and (options.all == 0)):
            break
        if ((now > start) or (options.all != 0)):
            if (options.type == "delay"):
                tmpfile.write("%s %f\n" % (dt, float(line[3])))
                if (savefile != None):
                    savefile.write("%s %f\n" % (dt, float(line[3])))
            else:
                tmpfile.write("%s %f\n" % (dt, float(line[4])))
                if (savefile != None):
                    savefile.write("%s %f\n" % (dt, float(line[4])))
            
    plotter = Gnuplot.Gnuplot(debug=1)
    plotter('set data style dots')
    if (options.type == "delay"):
        plotter.set_range('yrange', [options.ymin, options.ymax])
        plotter.ylabel('Seconds\\nOne Way Delay')
    else:
        plotter.set_range('yrange', [options.ymin, options.ymax])
        plotter.ylabel('Seconds\\nOffset')
    if (options.all == 0):
        plotter.xlabel(options.logfile + " " + options.start + " - " + options.end)
    else:
        plotter.xlabel(options.logfile + " " + str(start) + " - " + str(now))
    plotter('set xdata time')
    plotter('set timefmt "%Y-%m-%d %H:%M:%S"')

    tmpfile.flush()
    plotter.plot(Gnuplot.File(tmpfile.name, using='1:3'))

    if (options.png != None):
        plotter.hardcopy(options.logfile + "-" + options.type + ".png", terminal='png')
        raw_input('Press return to exit')
    else:
        raw_input('Press return to exit')


if __name__ == "__main__":
    main()
