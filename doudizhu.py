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
        "maxBytes": 100*1000**2,  # 10M
        "backupCount": 10,
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

    def __init__(self, cards, previous=None):
        '''
        cards: list[int]
        previous: Round ## not used
        '''
        super(Round, self).__init__()
        self.cards = cards
        self.previous = previous

    def __repr__(self):
        return '{} {}'.format(str(type(self)).split('.')[-1][:-2], self.cards)

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        raise NotImplemented

    @staticmethod
    def minimal(cards):
        raise NotImplemented


class PASS(Round):

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        cards = sorted(cards)
        if len(cards) == 0:
            return P
        return One.minimal(cards)

P = PASS([])


class One(Round):

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        cards = sorted(cards)
        for card in cards:
            if card > self.cards[0]:
                return One([card])

        if last_round_is_pass is True:
            return Two.minimal(cards)
        return Zha.minimal(cards)

    @staticmethod
    def minimal(cards):
        if cards == []:
            return P
        cards = sorted(cards)
        return One(cards[:1])


class Two(Round):
    """docstring for Two"""

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-1]):
            if e <= self.cards[0]:
                continue
            if e == cards[i+1]:
                return Two([e, e])
        if last_round_is_pass is True:
            return Three.minimal(cards)
        return Zha.minimal(cards)

    @staticmethod
    def minimal(cards):
        if len(cards) < 2:
            return P
        cards = sorted(cards)
        for i, e in enumerate(cards[:-1]):
            if e == cards[i+1]:
                return Two([e, e])
        # TODO should return Five.minimal?
        return Three.minimal(cards)


class Three(Round):

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-2]):
            if e <= self.cards[0]:
                continue
            if e == cards[i+1] == cards[i+2]:
                return Three([e, e, e])
        if last_round_is_pass is True:
            return ThreeOne.minimal(cards)
        return Zha.minimal(cards)

    @staticmethod
    def minimal(cards):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-2]):
            if e == cards[i+1] == cards[i+2]:
                return Three([e, e, e])
        return ThreeOne.minimal(cards)


class ThreeOne(Round):

    @staticmethod
    def _find_three(cards, card, must_be_bigger):
        for i, e in enumerate(cards[:-2]):
            if (must_be_bigger is True and e <= card) \
                    or (must_be_bigger is False and e < card):
                continue
            if cards[i:i+3] == [e] * 3:
                return [e] * 3
        return None

    @staticmethod
    def _find_one(cards, card, must_be_bigger):
        if cards == []:
            return None
        if must_be_bigger is False:
            return cards[0]
        for i, e in enumerate(cards):
            if e > card:
                return e
        return None

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        origin_cards = cards[:]
        cards = sorted(cards)
        if len(cards) <= 3:
            if last_round_is_pass is True:
                return Five.minimal(cards)
            else:
                return Zha.minimal(cards)

        three = ThreeOne._find_three(cards, self.cards[0], not is_rolled)
        if three is None:
            if last_round_is_pass is True:
                return Five.minimal(origin_cards)
            else:
                return Zha.minimal(origin_cards)

        if three[0] > self.cards[0]:
            must_be_bigger = False
        else:
            if is_rolled:
                must_be_bigger = True
            else:
                raise Exception("??")
        for e in three:
            cards.remove(e)
        one = ThreeOne._find_one(cards, self.cards[-1], must_be_bigger)
        if one is None:
            if last_round_is_pass is True:
                return Five.minimal(origin_cards)
            else:
                return Zha.minimal(origin_cards)
        return ThreeOne(three + [one])

    @staticmethod
    def minimal(cards):
        origin_cards = cards[:]
        cards = sorted(cards)
        three = ThreeOne._find_three(cards, 0, False)
        if three is None:
            return Five.minimal(cards)
        for e in three:
            cards.remove(e)
        one = ThreeOne._find_one(cards, 0, False)
        if one is None:
            return Five.minimal(origin_cards)
        return ThreeOne(three + [one])


class Five(Round):

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-4]):
            if e <= self.cards[0]:
                continue
            if cards[i:i+5] == range(e, e+5):
                return Five(range(e, e+5))
        if last_round_is_pass is True:
            return FourTwo.minimal(cards)
        else:
            return Zha.minimal(cards)
        return P

    @staticmethod
    def minimal(cards):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-4]):
            if cards[i:i+5] == range(e, e+5):
                return Five(range(e, e+5))
        return FourTwo.minimal(cards)


class FourTwo(Round):

    @staticmethod
    def _find_four(cards, card, must_be_bigger):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-3]):
            if (must_be_bigger is True and e <= card) \
                    or (must_be_bigger is False and e < card):
                continue
            if cards[i:i+4] == [e] * 4:
                return [e] * 4
        return None

    @staticmethod
    def _find_two(cards, two_cards, must_be_bigger):
        if len(cards) < 2:
            return None
        cards = sorted(cards)
        two_cards = sorted(two_cards)
        if must_be_bigger is False:
            return cards[:2]
        for i, e in enumerate(cards):
            if e < two_cards[0]:
                continue
            if e == two_cards[0]:
                for ee in cards[i+1:]:
                    if ee > two_cards[1]:
                        return [e, ee]
            if e > two_cards[1]:
                if i+2 <= len(cards):
                    return cards[i:2]
        return None

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        origin_cards = cards[:]
        cards = sorted(cards)
        four = FourTwo._find_four(cards, self.cards[0], not is_rolled)
        if four is None:
            if last_round_is_pass is True:
                return Zha.minimal(cards)
            else:
                return Zha.minimal(cards)

        if four[0] > self.cards[0]:
            must_be_bigger = False
        else:
            if is_rolled:
                must_be_bigger = True
            else:
                raise Exception("???")
        for e in four:
            cards.remove(e)
            two = FourTwo._find_two(cards, self.cards[-2:], must_be_bigger)
        if two is None:
            if last_round_is_pass is True:
                return Zha.minimal(origin_cards)
            else:
                return Zha.minimal(origin_cards)
        return FourTwo(four + two)

    @staticmethod
    def minimal(cards):
        cards = sorted(cards)
        four = FourTwo._find_four(cards, 0, False)
        if four is None:
            return Zha.minimal(cards)

        for e in four:
            cards.remove(e)
        two = FourTwo._find_two(cards, [0, 0], False)
        if two is None:
            return Zha.minimal(cards)
        return FourTwo(four+two)


class Zha(Round):

    def next(self, cards, last_round_is_pass=False, is_rolled=False):
        if self.cards[0] == 99:
            return P
        cards = sorted(cards)
        for i, e in enumerate(cards[:-3]):
            if e <= self.cards[0]:
                continue
            if e == cards[i+1] == cards[i+2] == cards[i+3]:
                return Zha([e, e, e, e])
        if len(cards) >= 2 and cards[-1] == 100 and cards[-2] == 99:
            return Zha([99, 100])
        return P

    @staticmethod
    def minimal(cards):
        cards = sorted(cards)
        for i, e in enumerate(cards[:-3]):
            if e == cards[i+1] == cards[i+2] == cards[i+3]:
                return Zha([e, e, e, e])
        if len(cards) >= 2 and cards[-1] == 100 and cards[-2] == 99:
            return Zha([99, 100])
        return P


class Player(object):

    def __init__(self, name, cards):
        self.name = name
        self.cards = cards
        self.paths = []
        self.last_round = None
        self.rolled_round = None
        self.loss = False

    def __repr__(self):
        return '({} {} {})'.format(self.name, self.cards, self.rolled_round)

    def __str__(self):
        return '{}'.format(self.name)

    def set_opponent(self, opponent):
        self.opponent = opponent

    def if_win(self):
        return self.cards == []

    def if_loss(self):
        return self.loss

    def next(self, desktop):
        should_be_bigger_than = self.rolled_round if self.rolled_round else desktop
        logging.info("should_be_bigger_than is %s" % should_be_bigger_than)
        desktop = should_be_bigger_than.next(
            self.cards[:], desktop is P, self.rolled_round is not None)
        # Game instance would judge if he losses
        # if desktop is P and self.paths[1:] and self.paths[-1] is P:
        # self.loss = True
        # return False
        # self.paths.append(desktop)
        for c in desktop.cards:
            self.cards.remove(c)
        self.rolled_round = None
        return desktop

    def rollback(self, round, active):
        self.cards.extend(round.cards)
        # self.paths.pop()
        if active is True:
            self.rolled_round = round
        else:
            self.rolled_round = None
        return round

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

    def __init__(self, players, current_player, init_desktop=P):
        super(Game, self).__init__()
        self.paths = []
        self.paths_list = []
        self.init_desktop = init_desktop
        self.desktop = P
        self.players = players
        self.current_player = current_player
        self.winner = None

    def add_player(self, player):
        self.players.append(player)

    def set_current_player(self, player):
        self.current_player = player

    def rollback(self, active_player, players):
        '''
        active_player is who ask for rollback
        '''
        for player in players:
            logging.info('roll back %s' % player)
            if self.paths == []:
                return False
            last = self.paths.pop()
            rst = player.rollback(last, active_player is player)
            logging.info('result of roll back of %s: %s' % (player, rst))
            # if rst is False:
            # return False

        if rst is P:
            return self.rollback(active_player, players)
        return rst

    def if_deadloop(self):
        for paths in self.paths_list:
            if len(paths) != len(self.paths):
                continue
            for i in range(len(paths)):
                if not isinstance(paths[i], type(self.paths[i])):
                    break
                if paths[i].cards != self.paths[i].cards:
                    break
            else:
                return True
        return False

    def go(self):
        i = 1
        while True:
            if i % 10000 == 0:
                logging.info("round %i" % i)
            # logging.info(len(self.paths_list))
            # for paths in self.paths_list:
                # logging.info('%s' % paths)
            i += 1
            self.desktop = self.paths[-1] if self.paths else self.init_desktop
            logging.info(
                "player is now %r. paths is %s. desktop is %s" %
                (self.current_player, self.paths, self.desktop))
            self.desktop = self.current_player.next(self.desktop)
            self.paths.append(self.desktop)
            # if self.if_deadloop():
                # raise Exception("deadloop")
            logging.info("%s plays %s" % (self.current_player, self.desktop))

            if len(self.paths) == 1 and self.paths[0] is P:
                # 第一张就只能Pass, 输了
                self.paths_list.append(self.paths[:])
                self.winner = self.current_player.opponent
                return

            # TODO 什么情况会判自己输? 的确有可能, 不过现在由Game判断他是不是输了
            # if self.current_player.if_loss():
            # logging.info("%s loss" % self.current_player)
            # return

            if self.paths[2:] and self.paths[-1] is P and self.paths[-2] is P:
                # 对方Pass的情况下无牌可出, 继续回退
                logging.info(
                    '%s passes after a Pass, roll back' %
                    self.current_player)
                logging.info('rollback: %s' % self.paths)
                self.paths_list.append(self.paths[:])
                self.rollback(
                    self.current_player, [
                        self.current_player, self.current_player.opponent, self.current_player])
                continue

            if self.current_player.if_win():
                logging.info('rollback: %s' % self.paths)
                self.paths_list.append(self.paths[:])
                if self.rollback(
                    self.current_player.opponent, [
                        self.current_player, self.current_player.opponent]) is False:
                    self.winner = self.current_player
                    return
                self.desktop = self.paths[-1] if self.paths else self.init_desktop

            self.current_player = self.current_player.opponent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", default="-", help="log file")
    parser.add_argument("--level", default="info")
    parser.add_argument("-a")
    parser.add_argument("-b")
    args = parser.parse_args()

    initlog(level=args.level, log=args.l)

    A = Player('A', [int(e) for e in args.a.split(',')])
    B = Player('B', [int(e) for e in args.b.split(',')])
    A.set_opponent(B)
    B.set_opponent(A)

    game = Game([A, B], A)
    game.go()
    logging.info('%s win' % game.winner)
    for paths in game.paths_list:
        logging.info('%s' % paths)
    logging.info('%s win' % game.winner)


if __name__ == '__main__':
    main()
