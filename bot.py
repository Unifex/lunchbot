#!/usr/bin/env python2

"""A really simple IRC bot."""

import sys
from twisted.internet import reactor, protocol
from twisted.words.protocols import irc

orders = {}
menu = [
    'Ham & triple cheese toastie',
    'The big fry up',
    '3 egg omelette',
    'Steak & stout pie',
    'Chicken salad',
    'Fish & chips',
    'Steak sandwich',
    'Beef burger',
    'Margherita pizza',
    'Beer garden pizza',
    'Smokin\' chicken pizza',
    'Spicy sausage pizza',
    'Pizza of the day'
       ]

def maybe_int(x):
    try: return int(x)
    except: return -1   # bs

class Bot(irc.IRCClient):
    def _get_nickname(self):
        return self.factory.nickname
    nickname = property(_get_nickname)

    def signedOn(self):
        self.join(self.factory.channel)
        print "Signed on as %s." % self.nickname

    def joined(self, channel):
        print "Joined %s." % channel

    def act(self, user, channel, cmd):
        username = user.split('!',1)[0]
        global orders, menu
        parts = cmd.split(' ',3)
        op = parts[0]
        if op == 'help':
            self.msg(channel, '!help: show this message.')
            self.msg(channel, '!menu: show the menu.')
            self.msg(channel, '!order [<nick>] <n> <special instructions>: order your lunch. `no beetroot` etc can go in `special instructions`')
            self.msg(channel, '!orderfor <name> <n> <special instructions>: order lunch for someone else. `no beetroot` etc can go in `special instructions`')
            self.msg(channel, '!cancel: cancel your order')
            self.msg(channel, '!cancelfor <name>: cancel someone else\'s order')
            self.msg(channel, '!list: list current lunch orders')
            self.msg(channel, '!open: open orders for today, clear state')

        if op == 'order':
            if len(parts) < 2:
                self.msg(channel, 'i\'m confused about what you wanted.')
                return

            item = maybe_int(parts[1])
            if item == -1 and len(parts) > 2:
                parts = cmd.split(' ',3)
                username = parts.pop(1)
                item = maybe_int(parts[1])
            if item < 0 or item >= len(menu):
                self.msg(channel, 'that\'s not a thing.')
                return

            special = len(parts) > 2 and parts[2] or None

            if not username in orders:
                orders[username] = []

            orders[username].append((item,special))
            if special:
                self.msg(channel, '%s added a %s, with instructions: %s.' % \
                    (username, menu[item], special))
            else:
                self.msg(channel, '%s added a %s.' % (username, menu[item]))

        if op == 'orderfor':
            if len(parts) < 3:
                self.msg(channel, '!orderfor <name> <n> <special instructions>')
                return

            item = maybe_int(parts[2])
            if item < 0 or item >= len(menu):
                self.msg(channel, 'that\'s not a thing.')
                return

            special = len(parts) > 3 and parts[3] or None

            ordername = parts[1]
            if not ordername in orders:
                orders[ordername] = []

            orders[ordername].append((item,special))
            if special:
                self.msg(channel, '%s added a %s(%s) on behalf of %s.' % \
                         (username, menu[item], special, ordername))
            else:
                self.msg(channel, '%s added a %s on behalf of %s.' % \
                         (username, menu[item], ordername))

        if op == 'menu':
            self.msg(channel, 'LBQ lunch menu:')
            for i,m in enumerate(menu):
                self.msg(channel, '%d) %s' % (i,m))
            self.msg(channel, '-- end of menu --');

        if op == 'cancel':
            if username not in orders:
                self.msg(channel, 'you don\'t have anything ordered!')
            else:
                del orders[username]
                self.msg(channel, 'your order has been canceled.')
                
        if op == 'cancelfor':
            if len(parts) < 2:
                self.msg(channel, '!cancelfor <name>')
                return
            
            ordername = parts[1]
            
            if ordername not in orders:
                self.msg(channel, '%s doesn\'t have anything ordered!' % \
                         (ordername))
            else:
                del orders[ordername]
                self.msg(channel, 'the order for %s has been canceled by %s.' % \
                         (ordername, username))

        if op == 'list':
            self.msg(channel, '%d orders for today:' \
                % sum(len(v) for _,v in orders.items()))
            by_type = pivot_to_values(flatten_values(orders))
            for o,n in sorted(by_type.items(), key=lambda x:len(x[1])):
                instr = o[1] and '(%s) ' % (o[1],) or ''
                self.msg(channel, '%dx %s %s[%s]' % \
                    (len(n), menu[o[0]], instr, ','.join(n)))
            self.msg(channel, '-- end of orders --');

        if op == 'open':
            orders = {}
            self.msg(channel, 'orders are now open!')

    def privmsg(self, user, channel, msg):
        print 'channel: `%s` user: `%s` msg: `%s`' % (user, channel, msg)
        if msg.startswith('!'):
            self.act( user, channel, msg[1:] )
        elif msg.startswith('lunchbot: '):
            self.act( user, channel, msg[10:] )

def flatten_values(xs):
    for k,x in xs.items():
        for x_ in x: yield (k,x_)

def pivot_to_values(xs):
    result = {}
    for k,v in xs:
        if v not in result: result[v] = [k]
        else: result[v].append(k)
    return result

class BotFactory(protocol.ClientFactory):
    protocol = Bot

    def __init__(self, channel, nickname='lunchbot'):
        self.channel = channel
        self.nickname = nickname

    def clientConnectionLost(self, connector, reason):
        print "Connection lost. Reason: %s" % reason
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print "Connection failed. Reason: %s" % reason

if __name__ == "__main__":
    chan = 'botdev'
    reactor.connectTCP('irc', 6667, BotFactory('#' + chan))
    reactor.run()
