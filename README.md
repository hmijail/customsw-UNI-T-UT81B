
# Custom client software for multimeters UNI-T UT81B

**NOTE: THIS PROJECT IS HEAVILY DEPRECATED. This was developed around 2010, so it used some very early version of the python module libusb1; later changes broke my code. For a 2015-modernized version, visit https://github.com/covex/dmm_ut81b**

----------

The original PC software for controlling multimeters UNI-T UT81B is crappy, isn't it?

Nah, that was a trick question. Of course it is.

I needed to record measurements with these multimeters, possibly simultaneously from more than one multimeter in a single computer, and that software didn't allow the required flexibility - even for a single multimeter. Luckily I managed to reverse-engineer the USB protocol and implement the functionality I needed over Python and py-libUSB. And here is the result.


Full details about the protocol innards, libUSB installation and usage of the code in [my blog](http://hmijailblog.blogspot.com/2011/12/custom-software-for-interfacing-via-usb.html).

Already someone found it useful (see comments in the blog post, including a reimplementation), and statistics say more people keep finding it, so I'm publishing here the code to make access easier.

If it was helpful, or if you need some extra nudge, please drop me a note!


