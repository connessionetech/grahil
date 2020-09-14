'''
This file is part of `Reactivity` 
Copyright 2018 Connessione Technologies

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import asyncio
import ntpath


def buildTopicPath(topic, subtopic):
    return topic + "/" + subtopic


def getLogFileKey(path):
    return str(path_leaf(path))


def path_leaf(path):
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)