#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import logging
import logging.config


def initlog(level=None, log="-"):
    if level is None:
        level = logging.DEBUG if __debug__ else logging.INFO
    if isinstance(level, basestring):
        level = getattr(logging, level.upper())

    class MyFormatter(logging.Formatter):

        def format(self, record):
            dformatter = '[%(asctime)s] %(name)s %(levelname)s %(pathname)s %(lineno)d [%(funcName)s] %(message)s'
            formatter = '[%(asctime)s] %(levelname)s %(name)s %(message)s'
            if record.levelno <= logging.DEBUG:
                self._fmt = dformatter
            else:
                self._fmt = formatter
            return super(MyFormatter, self).format(record)

    config = {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "custom": {
                '()': MyFormatter
            },
            "simple": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s"
            },
            "verbose": {
                "format": "%(asctime)s %(name)s %(levelname)s %(pathname)s %(lineno)d [%(funcName)s] %(message)s"
            }
        },
        "handlers": {
        },
        'root': {
            'level': level,
            'handlers': ['console']
        }
    }
    console = {
        "class": "logging.StreamHandler",
        "level": "DEBUG",
        "formatter": "custom",
        "stream": "ext://sys.stdout"
    }
    file_handler = {
        "class": "logging.handlers.RotatingFileHandler",
        "level": "DEBUG",
        "formatter": "custom",
        "filename": log,
        "maxBytes": 10*1000**2,  # 10M
        "backupCount": 5,
        "encoding": "utf8"
    }
    if log == "-":
        config["handlers"]["console"] = console
        config["root"]["handlers"] = ["console"]
    else:
        config["handlers"]["file_handler"] = file_handler
        config["root"]["handlers"] = ["file_handler"]
    logging.config.dictConfig(config)
# end initlog


class Round(object):

    def __init__(self, cards, previous):
        '''
        cards: list[int]
        previous: Round
        '''
        super(Round, self).__init__()
        self.cards = cards
        self.previous = previous

    def __repr__(self):
        return '{}'.format(self.cards)

    def next(self, cards, last_round_is_pass=False):
        raise NotImplemented


class PASS(Round):

    def next(self, cards, last_round_is_pass=False):
        cards = sorted(cards)
        return One(cards[:1])

P = PASS([])


class One(Round):

    def next(self, cards, last_round_is_pass=False):
        cards = sorted(cards)
        for card in cards:
            if card > self.cards[0]:
                return One([card])
        return P


class Player(object):

    def __init__(self, name, cards):
        self.name = name
        self.cards = cards
        self.paths = []
        self.last_round = None
        self.loss = False

    def __repr__(self):
        return '({} {} {})'.format(self.name, self.cards, self.paths)

    def __str__(self):
        return '{}'.format(self.name)

    def set_opponent(self, opponent):
        self.opponent = opponent

    def if_win(self):
        return self.cards == []

    def if_loss(self):
        return self.loss

    def next(self, desktop):
        should_be_bigger_than = self.last_round if self.last_round else desktop
        desktop = should_be_bigger_than.next(self.cards[:])
        if desktop is P and self.paths[1:] and self.paths[-1] is P:
            self.loss = True
            return False
        self.paths.append(desktop)
        for c in desktop.cards:
            self.cards.remove(c)
        return desktop

    def askfor_roll_back(self):
        '''
        will set return value as desktop
        '''
        if self.paths == []:
            return False

        opponent_last_round = self.opponent.rollback_request()

        if opponent_last_round is False:
            return False

        last = self.paths.pop()
        if last is P:
            return self.askfor_roll_back()
        self.last_round = last
        self.cards.extend(last.cards)

    def rollback_request(self):
        '''
        rtype: last path element after rolling back
        '''
        if self.paths == []:
            return False

        last = self.paths.pop()
        self.cards.extend(last.cards)

        if self.paths == []:
            return None
        return self.paths[-1]


class Game(object):
    """docstring for Game"""

    def __init__(self, players = [], current_player=None):
        super(Game, self).__init__()
        self.paths = []
        self.desktop = P
        self.players = players
        self.current_player = current_player
        self.winner = None

    def add_player(self, player):
        self.players.append(player)

    def set_current_player(self, player):
        self.current_player = player

    def rollback(self, *players):
        pass


    def go(self):
        while True:
            logging.info(
                "player is now %r. desktop is %s" %
                (self.current_player, self.desktop))
            self.desktop = self.current_player.next(self.desktop)
            logging.info("%s plays %s" % (self.current_player, self.desktop))

            # TODO 什么情况会判自己输?
            if self.current_player.if_loss():
                logging.info("%s loss" % self.current_player)
                return

            if self.current_player.if_win():
                # logging.info(
                    # '%s wins. %s try roll back' %
                    # (self.current_player, self.current_player.opponent))
                # self.desktop = self.current_player.opponent.askfor_roll_back()
                # if self.desktop is False:
                    # logging.info(
                        # "roll back faled. winner is %s" %
                        # self.current_player)
                    # return
                # logging.info(
                    # "after roll back: current player is %r; opponent is %r" %
                    # (self.current_player, self.current_player.opponent))

            self.current_player = self.current_player.opponent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", default="-", help="log file")
    parser.add_argument("--level", default="info")
    args = parser.parse_args()

    initlog(level=args.level, log=args.l)

    A = Player('A', [3, 5])
    B = Player('B', [4, 6])
    A.set_opponent(B)
    B.set_opponent(A)

    game = Game([A, B], A)
    game.go()


if __name__ == '__main__':
    main()
