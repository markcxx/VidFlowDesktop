# coding: utf-8
from enum import Enum

from qfluentwidgets import FluentIconBase, getIconColor, Theme


class VidFlowIcon(FluentIconBase, Enum):
    """ VidFlow icon """

    LOGO = "logo"
    PLAY = "play"
    STAR_PLUS = "star++"
    STAR = "star"
    VERIFIE = "verifie"
    HEART = "heart"
    COMMENT = "comment"
    SHARE = "share"
    COLLECT = "collect"
    BILIBILI = "bilibili"
    DOUYIN = "douyin"
    COIN = "coin"

    def path(self, theme=Theme.AUTO):
        if self.value in ["logo", "play"]:
            return f':/images/{self.value}.svg'
        elif self.value in ["bilibili", "douyin"]:
            return f':/images/setting_interface/{self.value}.svg'
        else:
            return f':/images/home_interface/{self.value}.svg'