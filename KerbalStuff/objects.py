import binascii
import os.path
from datetime import datetime

import bcrypt
from sqlalchemy import Column, Integer, String, Unicode, Boolean, DateTime, \
    ForeignKey, Table, Float
from sqlalchemy.orm import relationship, backref

from . import thumbnail
from .config import _cfg, site_logger
from .database import Base

mod_followers = Table('mod_followers', Base.metadata,
                      Column('mod_id', Integer, ForeignKey('mod.id')),
                      Column('user_id', Integer, ForeignKey('user.id')))


class Featured(Base):
    __tablename__ = 'featured'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref=backref('featured', order_by=id))
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<Featured %r>' % self.id


class BlogPost(Base):
    __tablename__ = 'blog'
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(1024))
    text = Column(Unicode(65535))
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<Blog Post %r>' % self.id


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(128), nullable=False, index=True)
    email = Column(String(256), nullable=False, index=True)
    public = Column(Boolean, default=False)
    admin = Column(Boolean, default=False)
    password = Column(String)
    description = Column(Unicode(10000), default='')
    created = Column(DateTime, default=datetime.now)
    forumUsername = Column(String(128), default='')
    forumId = Column(Integer)
    ircNick = Column(String(128), default='')
    twitterUsername = Column(String(128), default='')
    redditUsername = Column(String(128), default='')
    location = Column(String(128), default='')
    confirmation = Column(String(128))
    passwordReset = Column(String(128))
    passwordResetExpiry = Column(DateTime)
    backgroundMedia = Column(String(512), default='')
    bgOffsetX = Column(Integer, default=0)
    bgOffsetY = Column(Integer, default=0)
    following = relationship('Mod', secondary=mod_followers, backref='followers')
    dark_theme = Column(Boolean, default=False)

    def set_password(self, password):
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def create_confirmation(self):
        self.confirmation = binascii.b2a_hex(os.urandom(20)).decode('utf-8')

    def __repr__(self):
        return '<User %r>' % self.username

    # Flask.Login stuff
    # We don't use most of these features
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.confirmation is None

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.username


class UserAuth(Base):
    __tablename__ = 'user_auth'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    provider = Column(String(32))  # 'github' or 'google', etc.
    remote_user = Column(String(128), index=True)  # Usually the username on the other side
    created = Column(DateTime, default=datetime.now)

    # We can keep a token here, to allow interacting with the provider's API
    # on behalf of the user.

    def __repr__(self):
        return '<UserAuth %r, User %r>' % (self.provider, self.user_id)


class Publisher(Base):
    __tablename__ = 'publisher'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(1024))
    short_description = Column(Unicode(1000))
    description = Column(Unicode(100000))
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now)
    background = Column(String(512))
    bgOffsetX = Column(Integer)
    bgOffsetY = Column(Integer)
    link = Column(Unicode(1024))

    def __repr__(self):
        return '<Publisher %r %r>' % (self.id, self.name)


class Game(Base):
    __tablename__ = 'game'
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(1024))
    active = Column(Boolean())
    fileformats = Column(Unicode(1024))
    altname = Column(Unicode(1024))
    rating = Column(Float())
    releasedate = Column(DateTime)
    short = Column(Unicode(1024))
    publisher_id = Column(Integer, ForeignKey('publisher.id'))
    publisher = relationship('Publisher', backref='games')
    description = Column(Unicode(100000))
    short_description = Column(Unicode(1000))
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now)
    background = Column(String(512))
    bgOffsetX = Column(Integer)
    bgOffsetY = Column(Integer)
    link = Column(Unicode(1024))

    def __repr__(self):
        return '<Game %r %r>' % (self.id, self.name)


class Mod(Base):
    __tablename__ = 'mod'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now)
    updated = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref=backref('mods', order_by=created))
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship('Game', backref='mods')
    name = Column(String(100), index=True)
    description = Column(Unicode(100000))
    short_description = Column(Unicode(1000))
    approved = Column(Boolean, default=False)
    published = Column(Boolean, default=False)
    donation_link = Column(String(512))
    external_link = Column(String(512))
    license = Column(String(128))
    votes = Column(Integer, default=0)
    background = Column(String(512))
    bgOffsetX = Column(Integer)
    bgOffsetY = Column(Integer)
    default_version_id = Column(Integer, ForeignKey('modversion.id'))
    default_version = relationship('ModVersion',
                                   foreign_keys=default_version_id,
                                   post_update=True)
    source_link = Column(String(256))
    follower_count = Column(Integer, nullable=False, default=0)
    download_count = Column(Integer, nullable=False, default=0)
    ckan = Column(Boolean)

    def background_thumb(self):
        if _cfg('thumbnail_size') == '':
            return self.background
        thumbnail_sizes_str = _cfg('thumbnail_size').split('x')
        thumbnail_size = (int(thumbnail_sizes_str[0]), int(thumbnail_sizes_str[1]))
        split = os.path.split(self.background)
        thumb_path = os.path.join(split[0], 'thumb_' + split[1])
        full_thumb_path = os.path.join(
                os.path.join(_cfg('storage'), thumb_path.replace('/content/', '')))
        full_image_path = os.path.join(_cfg('storage'), self.background.replace('/content/', ''))
        if not os.path.isfile(full_thumb_path):
            try:
                thumbnail.create(full_image_path, full_thumb_path, thumbnail_size)
            except Exception:
                site_logger.exception('Unable to create thumbnail')
                try:
                    os.remove(full_image_path)
                except:
                    pass
                return self.background
        return thumb_path

    def __repr__(self):
        return '<Mod %r %r>' % (self.id, self.name)


class ModList(Base):
    __tablename__ = 'modlist'
    id = Column(Integer, primary_key=True)
    created = Column(DateTime, default=datetime.now)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref=backref('packs', order_by=created))
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship('Game', backref='modlists')
    background = Column(String(32))
    bgOffsetY = Column(Integer)
    description = Column(Unicode(100000))
    short_description = Column(Unicode(1000))
    name = Column(Unicode(1024))

    def __repr__(self):
        return '<ModList %r %r>' % (self.id, self.name)


class ModListItem(Base):
    __tablename__ = 'modlistitem'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref='mod_list_items')
    mod_list_id = Column(Integer, ForeignKey('modlist.id'))
    mod_list = relationship('ModList',
                            backref=backref('mods', order_by="asc(ModListItem.sort_index)"))
    sort_index = Column(Integer, default=0)

    def __repr__(self):
        return '<ModListItem %r %r>' % (self.mod_id, self.mod_list_id)


class SharedAuthor(Base):
    __tablename__ = 'sharedauthor'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref='shared_authors')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship('User', backref='shared_authors')
    accepted = Column(Boolean, default=False)

    def __repr__(self):
        return '<SharedAuthor %r>' % self.user_id


class DownloadEvent(Base):
    __tablename__ = 'downloadevent'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod',
                       backref=backref('downloads', order_by="desc(DownloadEvent.created)"))
    version_id = Column(Integer, ForeignKey('modversion.id'))
    version = relationship('ModVersion',
                           backref=backref('downloads', order_by="desc(DownloadEvent.created)"))
    downloads = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<Download Event %r>' % self.id


class FollowEvent(Base):
    __tablename__ = 'followevent'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod',
                       backref=backref('follow_events', order_by="desc(FollowEvent.created)"))
    events = Column(Integer)
    delta = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<Download Event %r>' % self.id


class ReferralEvent(Base):
    __tablename__ = 'referralevent'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod',
                       backref=backref('referrals', order_by="desc(ReferralEvent.created)"))
    host = Column(String)
    events = Column(Integer, default=0)
    created = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return '<Download Event %r>' % self.id


class ModVersion(Base):
    __tablename__ = 'modversion'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod',
                       backref=backref('versions', order_by="desc(ModVersion.sort_index)"),
                       foreign_keys=mod_id)
    friendly_version = Column(String(64))
    gameversion_id = Column(Integer, ForeignKey('gameversion.id'))
    gameversion = relationship('GameVersion', backref=backref('mod_versions', order_by=id))
    created = Column(DateTime, default=datetime.now)
    download_path = Column(String(512))
    changelog = Column(Unicode(10000))
    sort_index = Column(Integer, default=0)

    def __repr__(self):
        return '<Mod Version %r>' % self.id


class Media(Base):
    __tablename__ = 'media'
    id = Column(Integer, primary_key=True)
    mod_id = Column(Integer, ForeignKey('mod.id'))
    mod = relationship('Mod', backref=backref('media', order_by=id))
    hash = Column(String(12))
    type = Column(String(32))
    data = Column(String(512))

    def __repr__(self):
        return '<Media %r>' % self.hash


class GameVersion(Base):
    __tablename__ = 'gameversion'
    id = Column(Integer, primary_key=True)
    friendly_version = Column(String(128))
    game_id = Column(Integer, ForeignKey('game.id'))
    game = relationship('Game', backref='versions')

    def __repr__(self):
        return '<Game Version %r>' % self.friendly_version
