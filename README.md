# WATT_wheel
## My first automated stock trading program.

I have modified the well known 'wheel' strategy; I didn't have enough funds to start off with selling a cash covered put, so instead the program will accumulate shares so that I can start selling covered calls. 
Then the wheel can continue more normally.

The ticker that this program is interested in is 'WATT'. They only have options once a month, which makes it easier to calculate exp dates while I'm first starting out. Their stock price is currently between $3-4, cheap enough for me to play with right now.

Usage:
Set env vars for TOTP, EMAIL, and PASSWORD to login to Robinhood. Seems like TOTP is used on the first run, and then is no longer needed while running on the same system.

Set dry_run to False to actually place trades, set to True for only output on what would have been attempted.
