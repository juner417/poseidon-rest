import os, sys

def connect_using_pexpect(self, target, cmd):
    # make connection do something on remote host
    msg = 'Are you sure you want to continue connecting'
    child = pexpect.spawn('/bin/bash', ['-c', cmd])
    index = child.expect([msg, 'password:', pexpect.EOF, pexpect.TIMEOUT])

    if index == 0 :
	child.sendline('yes')
	index = child.expect([msg, 'password:', pexpect.EOF, pexpect.TIMEOUT])

    if index == 1:
	logging.debug('%s server is require passwd to login ' % (target))
	logging.debug('node: %s cmd: %s' % (target, cmd))
	child.sendline(self._passwd)
	child.expect(pexpect.EOF)
	res = True
    elif index == 2:
	logging.debug('%s server is NOT require passwd to login ' % (target))
	logging.debug('node: %s cmd: %s' % (target, cmd))
	child.after
	res = True
    else:
	logging.error('connot connect to %s' % target)
	res = False
    return res, child.before.strip('\n')
