#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import collections
import contextlib
import datetime
import errno
import fileinput
import io
import itertools
import json
import locale
import operator
import os
import platform
import re
import shutil
import subprocess
import socket
import sys
import time
import traceback

if os.name == 'nt':
    import ctypes

from .compat import (
    compat_basestring,
    compat_cookiejar,
    compat_expanduser,
    compat_get_terminal_size,
    compat_http_client,
    compat_kwargs,
    compat_str,
    compat_urllib_error,
    compat_urllib_request,
)
from .utils import (
    escape_url,
    ContentTooShortError,
    date_from_str,
    DateRange,
    DEFAULT_OUTTMPL,
    determine_ext,
    DownloadError,
    encodeFilename,
    ExtractorError,
    format_bytes,
    formatSeconds,
    locked_file,
    make_HTTPS_handler,
    MaxDownloadsReached,
    PagedList,
    parse_filesize,
    PerRequestProxyHandler,
    PostProcessingError,
    platform_name,
    preferredencoding,
    render_table,
    SameFileError,
    sanitize_filename,
    sanitize_path,
    std_headers,
    subtitles_filename,
    UnavailableVideoError,
    url_basename,
    version_tuple,
    write_json_file,
    write_string,
    YoutubeDLHandler,
    prepend_extension,
    replace_extension,
    args_to_str,
    age_restricted,
)
from .cache import Cache
from .extractor import get_info_extractor, gen_extractors
from .downloader import get_suitable_downloader
from .downloader.rtmp import rtmpdump_version
from .postprocessor import (
    FFmpegFixupM4aPP,
    FFmpegFixupStretchedPP,
    FFmpegMergerPP,
    FFmpegPostProcessor,
    get_postprocessor,
)
from .version import __version__


class YoutubeDL(object):
    """YoutubeDL class.

    YoutubeDL objects are the ones responsible of downloading the
    actual video file and writing it to disk if the user has requested
    it, among some other tasks. In most cases there should be one per
    program. As, given a video URL, the downloader doesn't know how to
    extract all the needed information, task that InfoExtractors do, it
    has to pass the URL to one of them.

    For this, YoutubeDL objects have a method that allows
    InfoExtractors to be registered in a given order. When it is passed
    a URL, the YoutubeDL object handles it to the first InfoExtractor it
    finds that reports being able to handle it. The InfoExtractor extracts
    all the information about the video or videos the URL refers to, and
    YoutubeDL process the extracted information, possibly using a File
    Downloader to download the video.

    YoutubeDL objects accept a lot of parameters. In order not to saturate
    the object constructor with arguments, it receives a dictionary of
    options instead. These options are available through the params
    attribute for the InfoExtractors to use. The YoutubeDL also
    registers itself as the downloader in charge for the InfoExtractors
    that are added to it, so this is a "mutual registration".

    Available options:

    username:          Username for authentication purposes.
    password:          Password for authentication purposes.
    videopassword:     Password for acces a video.
    usenetrc:          Use netrc for authentication instead.
    verbose:           Print additional info to stdout.
    quiet:             Do not print messages to stdout.
    no_warnings:       Do not print out anything for warnings.
    forceurl:          Force printing final URL.
    forcetitle:        Force printing title.
    forceid:           Force printing ID.
    forcethumbnail:    Force printing thumbnail URL.
    forcedescription:  Force printing description.
    forcefilename:     Force printing final filename.
    forceduration:     Force printing duration.
    forcejson:         Force printing info_dict as JSON.
    dump_single_json:  Force printing the info_dict of the whole playlist
                       (or video) as a single JSON line.
    simulate:          Do not download the video files.
    format:            Video format code. See options.py for more information.
    outtmpl:           Template for output names.
    restrictfilenames: Do not allow "&" and spaces in file names
    ignoreerrors:      Do not stop on download errors.
    nooverwrites:      Prevent overwriting files.
    playliststart:     Playlist item to start at.
    playlistend:       Playlist item to end at.
    playlist_items:    Specific indices of playlist to download.
    playlistreverse:   Download playlist items in reverse order.
    matchtitle:        Download only matching titles.
    rejecttitle:       Reject downloads for matching titles.
    logger:            Log messages to a logging.Logger instance.
    logtostderr:       Log messages to stderr instead of stdout.
    writedescription:  Write the video description to a .description file
    writeinfojson:     Write the video description to a .info.json file
    writeannotations:  Write the video annotations to a .annotations.xml file
    writethumbnail:    Write the thumbnail image to a file
    write_all_thumbnails:  Write all thumbnail formats to files
    writesubtitles:    Write the video subtitles to a file
    writeautomaticsub: Write the automatic subtitles to a file
    allsubtitles:      Downloads all the subtitles of the video
                       (requires writesubtitles or writeautomaticsub)
    listsubtitles:     Lists all available subtitles for the video
    subtitlesformat:   The format code for subtitles
    subtitleslangs:    List of languages of the subtitles to download
    keepvideo:         Keep the video file after post-processing
    daterange:         A DateRange object, download only if the upload_date is in the range.
    skip_download:     Skip the actual download of the video file
    cachedir:          Location of the cache files in the filesystem.
                       False to disable filesystem cache.
    noplaylist:        Download single video instead of a playlist if in doubt.
    age_limit:         An integer representing the user's age in years.
                       Unsuitable videos for the given age are skipped.
    min_views:         An integer representing the minimum view count the video
                       must have in order to not be skipped.
                       Videos without view count information are always
                       downloaded. None for no limit.
    max_views:         An integer representing the maximum view count.
                       Videos that are more popular than that are not
                       downloaded.
                       Videos without view count information are always
                       downloaded. None for no limit.
    download_archive:  File name of a file where all downloads are recorded.
                       Videos already present in the file are not downloaded
                       again.
    cookiefile:        File name where cookies should be read from and dumped to.
    nocheckcertificate:Do not verify SSL certificates
    prefer_insecure:   Use HTTP instead of HTTPS to retrieve information.
                       At the moment, this is only supported by YouTube.
    proxy:             URL of the proxy server to use
    cn_verification_proxy:  URL of the proxy to use for IP address verification
                       on Chinese sites. (Experimental)
    socket_timeout:    Time to wait for unresponsive hosts, in seconds
    bidi_workaround:   Work around buggy terminals without bidirectional text
                       support, using fridibi
    debug_printtraffic:Print out sent and received HTTP traffic
    include_ads:       Download ads as well
    default_search:    Prepend this string if an input url is not valid.
                       'auto' for elaborate guessing
    encoding:          Use this encoding instead of the system-specified.
    extract_flat:      Do not resolve URLs, return the immediate result.
                       Pass in 'in_playlist' to only show this behavior for
                       playlist items.
    postprocessors:    A list of dictionaries, each with an entry
                       * key:  The name of the postprocessor. See
                               youtube_dl/postprocessor/__init__.py for a list.
                       as well as any further keyword arguments for the
                       postprocessor.
    progress_hooks:    A list of functions that get called on download
                       progress, with a dictionary with the entries
                       * status: One of "downloading", "error", or "finished".
                                 Check this first and ignore unknown values.

                       If status is one of "downloading", or "finished", the
                       following properties may also be present:
                       * filename: The final filename (always present)
                       * tmpfilename: The filename we're currently writing to
                       * downloaded_bytes: Bytes on disk
                       * total_bytes: Size of the whole file, None if unknown
                       * total_bytes_estimate: Guess of the eventual file size,
                                               None if unavailable.
                       * elapsed: The number of seconds since download started.
                       * eta: The estimated time in seconds, None if unknown
                       * speed: The download speed in bytes/second, None if
                                unknown
                       * fragment_index: The counter of the currently
                                         downloaded video fragment.
                       * fragment_count: The number of fragments (= individual
                                         files that will be merged)

                       Progress hooks are guaranteed to be called at least once
                       (with status "finished") if the download is successful.
    merge_output_format: Extension to use when merging formats.
    fixup:             Automatically correct known faults of the file.
                       One of:
                       - "never": do nothing
                       - "warn": only emit a warning
                       - "detect_or_warn": check whether we can do anything
                                           about it, warn otherwise (default)
    source_address:    (Experimental) Client-side IP address to bind to.
    call_home:         Boolean, true iff we are allowed to contact the
                       youtube-dl servers for debugging.
    sleep_interval:    Number of seconds to sleep before each download.
    listformats:       Print an overview of available video formats and exit.
    list_thumbnails:   Print a table of all thumbnails and exit.
    match_filter:      A function that gets called with the info_dict of
                       every video.
                       If it returns a message, the video is ignored.
                       If it returns None, the video is downloaded.
                       match_filter_func in utils.py is one example for this.
    no_color:          Do not emit color codes in output.

    The following options determine which downloader is picked:
    external_downloader: Executable of the external downloader to call.
                       None or unset for standard (built-in) downloader.
    hls_prefer_native: Use the native HLS downloader instead of ffmpeg/avconv.

    The following parameters are not used by YoutubeDL itself, they are used by
    the downloader (see youtube_dl/downloader/common.py):
    nopart, updatetime, buffersize, ratelimit, min_filesize, max_filesize, test,
    noresizebuffer, retries, continuedl, noprogress, consoletitle,
    xattr_set_filesize, external_downloader_args.

    The following options are used by the post processors:
    prefer_ffmpeg:     If True, use ffmpeg instead of avconv if both are available,
                       otherwise prefer avconv.
    """

    params = None
    _ies = []
    _pps = []
    _download_retcode = None
    _num_downloads = None
    _screen_file = None

    def __init__(self, params=None, auto_init=True):
        """Create a FileDownloader object with the given options."""
        if params is None:
            params = {}
        self._ies = []
        self._ies_instances = {}
        self._pps = []
        self._progress_hooks = []
        self._download_retcode = 0
        self._num_downloads = 0
        self._screen_file = [sys.stdout, sys.stderr][params.get('logtostderr', False)]
        self._err_file = sys.stderr
        self.params = params
        self.cache = Cache(self)

        if params.get('bidi_workaround', False):
            try:
                import pty
                master, slave = pty.openpty()
                width = compat_get_terminal_size().columns
                if width is None:
                    width_args = []
                else:
                    width_args = ['-w', str(width)]
                sp_kwargs = dict(
                    stdin=subprocess.PIPE,
                    stdout=slave,
                    stderr=self._err_file)
                try:
                    self._output_process = subprocess.Popen(
                        ['bidiv'] + width_args, **sp_kwargs
                    )
                except OSError:
                    self._output_process = subprocess.Popen(
                        ['fribidi', '-c', 'UTF-8'] + width_args, **sp_kwargs)
                self._output_channel = os.fdopen(master, 'rb')
            except OSError as ose:
                if ose.errno == 2:
                    self.report_warning('Could not find fribidi executable, ignoring --bidi-workaround . Make sure that  fribidi  is an executable file in one of the directories in your $PATH.')
                else:
                    raise

        if (sys.version_info >= (3,) and sys.platform != 'win32' and
                sys.getfilesystemencoding() in ['ascii', 'ANSI_X3.4-1968'] and
                not params.get('restrictfilenames', False)):
            # On Python 3, the Unicode filesystem API will throw errors (#1474)
            self.report_warning(
                'Assuming --restrict-filenames since file system encoding '
                'cannot encode all characters. '
                'Set the LC_ALL environment variable to fix this.')
            self.params['restrictfilenames'] = True

        if isinstance(params.get('outtmpl'), bytes):
            self.report_warning(
                'Parameter outtmpl is bytes, but should be a unicode string. '
                'Put  from __future__ import unicode_literals  at the top of your code file or consider switching to Python 3.x.')

        self._setup_opener()

        if auto_init:
            self.print_debug_header()
            self.add_default_info_extractors()

        for pp_def_raw in self.params.get('postprocessors', []):
            pp_class = get_postprocessor(pp_def_raw['key'])
            pp_def = dict(pp_def_raw)
            del pp_def['key']
            pp = pp_class(self, **compat_kwargs(pp_def))
            self.add_post_processor(pp)

        for ph in self.params.get('progress_hooks', []):
            self.add_progress_hook(ph)

    def warn_if_short_id(self, argv):
        # short YouTube ID starting with dash?
        idxs = [
            i for i, a in enumerate(argv)
            if re.match(r'^-[0-9A-Za-z_-]{10}$', a)]
        if idxs:
            correct_argv = (
                ['youtube-dl'] +
                [a for i, a in enumerate(argv) if i not in idxs] +
                ['--'] + [argv[i] for i in idxs]
            )
            self.report_warning(
                'Long argument string detected. '
                'Use -- to separate parameters and URLs, like this:\n%s\n' %
                args_to_str(correct_argv))

    def add_info_extractor(self, ie):
        """Add an InfoExtractor object to the end of the list."""
        self._ies.append(ie)
        self._ies_instances[ie.ie_key()] = ie
        ie.set_downloader(self)

    def get_info_extractor(self, ie_key):
        """
        Get an instance of an IE with name ie_key, it will try to get one from
        the _ies list, if there's no instance it will create a new one and add
        it to the extractor list.
        """
        ie = self._ies_instances.get(ie_key)
        if ie is None:
            ie = get_info_extractor(ie_key)()
            self.add_info_extractor(ie)
        return ie

    def add_default_info_extractors(self):
        """
        Add the InfoExtractors returned by gen_extractors to the end of the list
        """
        for ie in gen_extractors():
            self.add_info_extractor(ie)

    def add_post_processor(self, pp):
        """Add a PostProcessor object to the end of the chain."""
        self._pps.append(pp)
        pp.set_downloader(self)

    def add_progress_hook(self, ph):
        """Add the progress hook (currently only for the file downloader)"""
        self._progress_hooks.append(ph)

    def _bidi_workaround(self, message):
        if not hasattr(self, '_output_channel'):
            return message

        assert hasattr(self, '_output_process')
        assert isinstance(message, compat_str)
        line_count = message.count('\n') + 1
        self._output_process.stdin.write((message + '\n').encode('utf-8'))
        self._output_process.stdin.flush()
        res = ''.join(self._output_channel.readline().decode('utf-8')
                      for _ in range(line_count))
        return res[:-len('\n')]

    def to_screen(self, message, skip_eol=False):
        """Print message to stdout if not in quiet mode."""
        return self.to_stdout(message, skip_eol, check_quiet=True)

    def _write_string(self, s, out=None):
        write_string(s, out=out, encoding=self.params.get('encoding'))

    def to_stdout(self, message, skip_eol=False, check_quiet=False):
        """Print message to stdout if not in quiet mode."""
        if self.params.get('logger'):
            self.params['logger'].debug(message)
        elif not check_quiet or not self.params.get('quiet', False):
            message = self._bidi_workaround(message)
            terminator = ['\n', ''][skip_eol]
            output = message + terminator

            self._write_string(output, self._screen_file)

    def to_stderr(self, message):
        """Print message to stderr."""
        assert isinstance(message, compat_str)
        if self.params.get('logger'):
            self.params['logger'].error(message)
        else:
            message = self._bidi_workaround(message)
            output = message + '\n'
            self._write_string(output, self._err_file)

    def to_console_title(self, message):
        if not self.params.get('consoletitle', False):
            return
        if os.name == 'nt' and ctypes.windll.kernel32.GetConsoleWindow():
            # c_wchar_p() might not be necessary if `message` is
            # already of type unicode()
            ctypes.windll.kernel32.SetConsoleTitleW(ctypes.c_wchar_p(message))
        elif 'TERM' in os.environ:
            self._write_string('\033]0;%s\007' % message, self._screen_file)

    def save_console_title(self):
        if not self.params.get('consoletitle', False):
            return
        if 'TERM' in os.environ:
            # Save the title on stack
            self._write_string('\033[22;0t', self._screen_file)

    def restore_console_title(self):
        if not self.params.get('consoletitle', False):
            return
        if 'TERM' in os.environ:
            # Restore the title from stack
            self._write_string('\033[23;0t', self._screen_file)

    def __enter__(self):
        self.save_console_title()
        return self

    def __exit__(self, *args):
        self.restore_console_title()

        if self.params.get('cookiefile') is not None:
            self.cookiejar.save()

    def trouble(self, message=None, tb=None):
        """Determine action to take when a download problem appears.

        Depending on if the downloader has been configured to ignore
        download errors or not, this method may throw an exception or
        not when errors are found, after printing the message.

        tb, if given, is additional traceback information.
        """
        if message is not None:
            self.to_stderr(message)
        if self.params.get('verbose'):
            if tb is None:
                if sys.exc_info()[0]:  # if .trouble has been called from an except block
                    tb = ''
                    if hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                        tb += ''.join(traceback.format_exception(*sys.exc_info()[1].exc_info))
                    tb += compat_str(traceback.format_exc())
                else:
                    tb_data = traceback.format_list(traceback.extract_stack())
                    tb = ''.join(tb_data)
            self.to_stderr(tb)
        if not self.params.get('ignoreerrors', False):
            if sys.exc_info()[0] and hasattr(sys.exc_info()[1], 'exc_info') and sys.exc_info()[1].exc_info[0]:
                exc_info = sys.exc_info()[1].exc_info
            else:
                exc_info = sys.exc_info()
            raise DownloadError(message, exc_info)
        self._download_retcode = 1

    def report_warning(self, message):
        '''
        Print the message to stderr, it will be prefixed with 'WARNING:'
        If stderr is a tty file the 'WARNING:' will be colored
        '''
        if self.params.get('logger') is not None:
            self.params['logger'].warning(message)
        else:
            if self.params.get('no_warnings'):
                return
            if not self.params.get('no_color') and self._err_file.isatty() and os.name != 'nt':
                _msg_header = '\033[0;33mWARNING:\033[0m'
            else:
                _msg_header = 'WARNING:'
            warning_message = '%s %s' % (_msg_header, message)
            self.to_stderr(warning_message)

    def report_error(self, message, tb=None):
        '''
        Do the same as trouble, but prefixes the message with 'ERROR:', colored
        in red if stderr is a tty file.
        '''
        if not self.params.get('no_color') and self._err_file.isatty() and os.name != 'nt':
            _msg_header = '\033[0;31mERROR:\033[0m'
        else:
            _msg_header = 'ERROR:'
        error_message = '%s %s' % (_msg_header, message)
        self.trouble(error_message, tb)

    def report_file_already_downloaded(self, file_name):
        """Report file has already been fully downloaded."""
        try:
            self.to_screen('[download] %s has already been downloaded' % file_name)
        except UnicodeEncodeError:
            self.to_screen('[download] The file has already been downloaded')

    def prepare_filename(self, info_dict):
        """Generate the output filename."""
        try:
            template_dict = dict(info_dict)

            template_dict['epoch'] = int(time.time())
            autonumber_size = self.params.get('autonumber_size')
            if autonumber_size is None:
                autonumber_size = 5
            autonumber_templ = '%0' + str(autonumber_size) + 'd'
            template_dict['autonumber'] = autonumber_templ % self._num_downloads
            if template_dict.get('playlist_index') is not None:
                template_dict['playlist_index'] = '%0*d' % (len(str(template_dict['n_entries'])), template_dict['playlist_index'])
            if template_dict.get('resolution') is None:
                if template_dict.get('width') and template_dict.get('height'):
                    template_dict['resolution'] = '%dx%d' % (template_dict['width'], template_dict['height'])
                elif template_dict.get('height'):
                    template_dict['resolution'] = '%sp' % template_dict['height']
                elif template_dict.get('width'):
                    template_dict['resolution'] = '?x%d' % template_dict['width']

            sanitize = lambda k, v: sanitize_filename(
                compat_str(v),
                restricted=self.params.get('restrictfilenames'),
                is_id=(k == 'id'))
            template_dict = dict((k, sanitize(k, v))
                                 for k, v in template_dict.items()
                                 if v is not None)
            template_dict = collections.defaultdict(lambda: 'NA', template_dict)

            outtmpl = sanitize_path(self.params.get('outtmpl', DEFAULT_OUTTMPL))
            tmpl = compat_expanduser(outtmpl)
            filename = tmpl % template_dict
            # Temporary fix for #4787
            # 'Treat' all problem characters by passing filename through preferredencoding
            # to workaround encoding issues with subprocess on python2 @ Windows
            if sys.version_info < (3, 0) and sys.platform == 'win32':
                filename = encodeFilename(filename, True).decode(preferredencoding())
            return filename
        except ValueError as err:
            self.report_error('Error in output template: ' + str(err) + ' (encoding: ' + repr(preferredencoding()) + ')')
            return None

    def _match_entry(self, info_dict, incomplete):
        """ Returns None iff the file should be downloaded """

        video_title = info_dict.get('title', info_dict.get('id', 'video'))
        if 'title' in info_dict:
            # This can happen when we're just evaluating the playlist
            title = info_dict['title']
            matchtitle = self.params.get('matchtitle', False)
            if matchtitle:
                if not re.search(matchtitle, title, re.IGNORECASE):
                    return '"' + title + '" title did not match pattern "' + matchtitle + '"'
            rejecttitle = self.params.get('rejecttitle', False)
            if rejecttitle:
                if re.search(rejecttitle, title, re.IGNORECASE):
                    return '"' + title + '" title matched reject pattern "' + rejecttitle + '"'
        date = info_dict.get('upload_date', None)
        if date is not None:
            dateRange = self.params.get('daterange', DateRange())
            if date not in dateRange:
                return '%s upload date is not in range %s' % (date_from_str(date).isoformat(), dateRange)
        view_count = info_dict.get('view_count', None)
        if view_count is not None:
            min_views = self.params.get('min_views')
            if min_views is not None and view_count < min_views:
                return 'Skipping %s, because it has not reached minimum view count (%d/%d)' % (video_title, view_count, min_views)
            max_views = self.params.get('max_views')
            if max_views is not None and view_count > max_views:
                return 'Skipping %s, because it has exceeded the maximum view count (%d/%d)' % (video_title, view_count, max_views)
        if age_restricted(info_dict.get('age_limit'), self.params.get('age_limit')):
            return 'Skipping "%s" because it is age restricted' % video_title
        if self.in_download_archive(info_dict):
            return '%s has already been recorded in archive' % video_title

        if not incomplete:
            match_filter = self.params.get('match_filter')
            if match_filter is not None:
                ret = match_filter(info_dict)
                if ret is not None:
                    return ret

        return None

    @staticmethod
    def add_extra_info(info_dict, extra_info):
        '''Set the keys from extra_info in info dict if they are missing'''
        for key, value in extra_info.items():
            info_dict.setdefault(key, value)

    def extract_info(self, url, download=True, ie_key=None, extra_info={},
                     process=True):
        '''
        Returns a list with a dictionary for each video we find.
        If 'download', also downloads the videos.
        extra_info is a dict containing the extra values to add to each result
        '''

        if ie_key:
            ies = [self.get_info_extractor(ie_key)]
        else:
            ies = self._ies

        for ie in ies:
            if not ie.suitable(url):
                continue

            if not ie.working():
                self.report_warning('The program functionality for this site has been marked as broken, '
                                    'and will probably not work.')

            try:
                ie_result = ie.extract(url)
                if ie_result is None:  # Finished already (backwards compatibility; listformats and friends should be moved here)
                    break
                if isinstance(ie_result, list):
                    # Backwards compatibility: old IE result format
                    ie_result = {
                        '_type': 'compat_list',
                        'entries': ie_result,
                    }
                self.add_default_extra_info(ie_result, ie, url)
                if process:
                    return self.process_ie_result(ie_result, download, extra_info)
                else:
                    return ie_result
            except ExtractorError as de:  # An error we somewhat expected
                self.report_error(compat_str(de), de.format_traceback())
                break
            except MaxDownloadsReached:
                raise
            except Exception as e:
                if self.params.get('ignoreerrors', False):
                    self.report_error(compat_str(e), tb=compat_str(traceback.format_exc()))
                    break
                else:
                    raise
        else:
            self.report_error('no suitable InfoExtractor for URL %s' % url)

    def add_default_extra_info(self, ie_result, ie, url):
        self.add_extra_info(ie_result, {
            'extractor': ie.IE_NAME,
            'webpage_url': url,
            'webpage_url_basename': url_basename(url),
            'extractor_key': ie.ie_key(),
        })

    def process_ie_result(self, ie_result, download=True, extra_info={}):
        """
        Take the result of the ie(may be modified) and resolve all unresolved
        references (URLs, playlist items).

        It will also download the videos if 'download'.
        Returns the resolved ie_result.
        """

        result_type = ie_result.get('_type', 'video')

        if result_type in ('url', 'url_transparent'):
            extract_flat = self.params.get('extract_flat', False)
            if ((extract_flat == 'in_playlist' and 'playlist' in extra_info) or
                    extract_flat is True):
                if self.params.get('forcejson', False):
                    self.to_stdout(json.dumps(ie_result))
                return ie_result

        if result_type == 'video':
            self.add_extra_info(ie_result, extra_info)
            return self.process_video_result(ie_result, download=download)
        elif result_type == 'url':
            # We have to add extra_info to the results because it may be
            # contained in a playlist
            return self.extract_info(ie_result['url'],
                                     download,
                                     ie_key=ie_result.get('ie_key'),
                                     extra_info=extra_info)
        elif result_type == 'url_transparent':
            # Use the information from the embedding page
            info = self.extract_info(
                ie_result['url'], ie_key=ie_result.get('ie_key'),
                extra_info=extra_info, download=False, process=False)

            force_properties = dict(
                (k, v) for k, v in ie_result.items() if v is not None)
            for f in ('_type', 'url'):
                if f in force_properties:
                    del force_properties[f]
            new_result = info.copy()
            new_result.update(force_properties)

            assert new_result.get('_type') != 'url_transparent'

            return self.process_ie_result(
                new_result, download=download, extra_info=extra_info)
        elif result_type == 'playlist' or result_type == 'multi_video':
            # We process each entry in the playlist
            playlist = ie_result.get('title', None) or ie_result.get('id', None)
            self.to_screen('[download] Downloading playlist: %s' % playlist)

            playlist_results = []

            playliststart = self.params.get('playliststart', 1) - 1
            playlistend = self.params.get('playlistend', None)
            # For backwards compatibility, interpret -1 as whole list
            if playlistend == -1:
                playlistend = None

            playlistitems_str = self.params.get('playlist_items', None)
            playlistitems = None
            if playlistitems_str is not None:
                def iter_playlistitems(format):
                    for string_segment in format.split(','):
                        if '-' in string_segment:
                            start, end = string_segment.split('-')
                            for item in range(int(start), int(end) + 1):
                                yield int(item)
                        else:
                            yield int(string_segment)
                playlistitems = iter_playlistitems(playlistitems_str)

            ie_entries = ie_result['entries']
            if isinstance(ie_entries, list):
                n_all_entries = len(ie_entries)
                if playlistitems:
                    entries = [
                        ie_entries[i - 1] for i in playlistitems
                        if -n_all_entries <= i - 1 < n_all_entries]
                else:
                    entries = ie_entries[playliststart:playlistend]
                n_entries = len(entries)
                self.to_screen(
                    "[%s] playlist %s: Collected %d video ids (downloading %d of them)" %
                    (ie_result['extractor'], playlist, n_all_entries, n_entries))
            elif isinstance(ie_entries, PagedList):
                if playlistitems:
                    entries = []
                    for item in playlistitems:
                        entries.extend(ie_entries.getslice(
                            item - 1, item
                        ))
                else:
                    entries = ie_entries.getslice(
                        playliststart, playlistend)
                n_entries = len(entries)
                self.to_screen(
                    "[%s] playlist %s: Downloading %d videos" %
                    (ie_result['extractor'], playlist, n_entries))
            else:  # iterable
                if playlistitems:
                    entry_list = list(ie_entries)
                    entries = [entry_list[i - 1] for i in playlistitems]
                else:
                    entries = list(itertools.islice(
                        ie_entries, playliststart, playlistend))
                n_entries = len(entries)
                self.to_screen(
                    "[%s] playlist %s: Downloading %d videos" %
                    (ie_result['extractor'], playlist, n_entries))

            if self.params.get('playlistreverse', False):
                entries = entries[::-1]

            for i, entry in enumerate(entries, 1):
                self.to_screen('[download] Downloading video %s of %s' % (i, n_entries))
                extra = {
                    'n_entries': n_entries,
                    'playlist': playlist,
                    'playlist_id': ie_result.get('id'),
                    'playlist_title': ie_result.get('title'),
                    'playlist_index': i + playliststart,
                    'extractor': ie_result['extractor'],
                    'webpage_url': ie_result['webpage_url'],
                    'webpage_url_basename': url_basename(ie_result['webpage_url']),
                    'extractor_key': ie_result['extractor_key'],
                }

                reason = self._match_entry(entry, incomplete=True)
                if reason is not None:
                    self.to_screen('[download] ' + reason)
                    continue

                entry_result = self.process_ie_result(entry,
                                                      download=download,
                                                      extra_info=extra)
                playlist_results.append(entry_result)
            ie_result['entries'] = playlist_results
            return ie_result
        elif result_type == 'compat_list':
            self.report_warning(
                'Extractor %s returned a compat_list result. '
                'It needs to be updated.' % ie_result.get('extractor'))

            def _fixup(r):
                self.add_extra_info(
                    r,
                    {
                        'extractor': ie_result['extractor'],
                        'webpage_url': ie_result['webpage_url'],
                        'webpage_url_basename': url_basename(ie_result['webpage_url']),
                        'extractor_key': ie_result['extractor_key'],
                    }
                )
                return r
            ie_result['entries'] = [
                self.process_ie_result(_fixup(r), download, extra_info)
                for r in ie_result['entries']
            ]
            return ie_result
        else:
            raise Exception('Invalid result type: %s' % result_type)

    def _apply_format_filter(self, format_spec, available_formats):
        " Returns a tuple of the remaining format_spec and filtered formats "

        OPERATORS = {
            '<': operator.lt,
            '<=': operator.le,
            '>': operator.gt,
            '>=': operator.ge,
            '=': operator.eq,
            '!=': operator.ne,
        }
        operator_rex = re.compile(r'''(?x)\s*\[
            (?P<key>width|height|tbr|abr|vbr|asr|filesize|fps)
            \s*(?P<op>%s)(?P<none_inclusive>\s*\?)?\s*
            (?P<value>[0-9.]+(?:[kKmMgGtTpPeEzZyY]i?[Bb]?)?)
            \]$
            ''' % '|'.join(map(re.escape, OPERATORS.keys())))
        m = operator_rex.search(format_spec)
        if m:
            try:
                comparison_value = int(m.group('value'))
            except ValueError:
                comparison_value = parse_filesize(m.group('value'))
                if comparison_value is None:
                    comparison_value = parse_filesize(m.group('value') + 'B')
                if comparison_value is None:
                    raise ValueError(
                        'Invalid value %r in format specification %r' % (
                            m.group('value'), format_spec))
            op = OPERATORS[m.group('op')]

        if not m:
            STR_OPERATORS = {
                '=': operator.eq,
                '!=': operator.ne,
            }
            str_operator_rex = re.compile(r'''(?x)\s*\[
                \s*(?P<key>ext|acodec|vcodec|container|protocol)
                \s*(?P<op>%s)(?P<none_inclusive>\s*\?)?
                \s*(?P<value>[a-zA-Z0-9_-]+)
                \s*\]$
                ''' % '|'.join(map(re.escape, STR_OPERATORS.keys())))
            m = str_operator_rex.search(format_spec)
            if m:
                comparison_value = m.group('value')
                op = STR_OPERATORS[m.group('op')]

        if not m:
            raise ValueError('Invalid format specification %r' % format_spec)

        def _filter(f):
            actual_value = f.get(m.group('key'))
            if actual_value is None:
                return m.group('none_inclusive')
            return op(actual_value, comparison_value)
        new_formats = [f for f in available_formats if _filter(f)]

        new_format_spec = format_spec[:-len(m.group(0))]
        if not new_format_spec:
            new_format_spec = 'best'

        return (new_format_spec, new_formats)

    def select_format(self, format_spec, available_formats):
        while format_spec.endswith(']'):
            format_spec, available_formats = self._apply_format_filter(
                format_spec, available_formats)
        if not available_formats:
            return None

        if format_spec in ['best', 'worst', None]:
            format_idx = 0 if format_spec == 'worst' else -1
            audiovideo_formats = [
                f for f in available_formats
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
            if audiovideo_formats:
                return audiovideo_formats[format_idx]
            # for audio only urls, select the best/worst audio format
            elif all(f.get('acodec') != 'none' for f in available_formats):
                return available_formats[format_idx]
        elif format_spec == 'bestaudio':
            audio_formats = [
                f for f in available_formats
                if f.get('vcodec') == 'none']
            if audio_formats:
                return audio_formats[-1]
        elif format_spec == 'worstaudio':
            audio_formats = [
                f for f in available_formats
                if f.get('vcodec') == 'none']
            if audio_formats:
                return audio_formats[0]
        elif format_spec == 'bestvideo':
            video_formats = [
                f for f in available_formats
                if f.get('acodec') == 'none']
            if video_formats:
                return video_formats[-1]
        elif format_spec == 'worstvideo':
            video_formats = [
                f for f in available_formats
                if f.get('acodec') == 'none']
            if video_formats:
                return video_formats[0]
        else:
            extensions = ['mp4', 'flv', 'webm', '3gp', 'm4a', 'mp3', 'ogg', 'aac', 'wav']
            if format_spec in extensions:
                filter_f = lambda f: f['ext'] == format_spec
            else:
                filter_f = lambda f: f['format_id'] == format_spec
            matches = list(filter(filter_f, available_formats))
            if matches:
                return matches[-1]
        return None

    def _calc_headers(self, info_dict):
        res = std_headers.copy()

        add_headers = info_dict.get('http_headers')
        if add_headers:
            res.update(add_headers)

        cookies = self._calc_cookies(info_dict)
        if cookies:
            res['Cookie'] = cookies

        return res

    def _calc_cookies(self, info_dict):
        pr = compat_urllib_request.Request(info_dict['url'])
        self.cookiejar.add_cookie_header(pr)
        return pr.get_header('Cookie')

    def process_video_result(self, info_dict, download=True):
        assert info_dict.get('_type', 'video') == 'video'

        if 'id' not in info_dict:
            raise ExtractorError('Missing "id" field in extractor result')
        if 'title' not in info_dict:
            raise ExtractorError('Missing "title" field in extractor result')

        if 'playlist' not in info_dict:
            # It isn't part of a playlist
            info_dict['playlist'] = None
            info_dict['playlist_index'] = None

        thumbnails = info_dict.get('thumbnails')
        if thumbnails is None:
            thumbnail = info_dict.get('thumbnail')
            if thumbnail:
                info_dict['thumbnails'] = thumbnails = [{'url': thumbnail}]
        if thumbnails:
            thumbnails.sort(key=lambda t: (
                t.get('preference'), t.get('width'), t.get('height'),
                t.get('id'), t.get('url')))
            for i, t in enumerate(thumbnails):
                if 'width' in t and 'height' in t:
                    t['resolution'] = '%dx%d' % (t['width'], t['height'])
                if t.get('id') is None:
                    t['id'] = '%d' % i

        if thumbnails and 'thumbnail' not in info_dict:
            info_dict['thumbnail'] = thumbnails[-1]['url']

        if 'display_id' not in info_dict and 'id' in info_dict:
            info_dict['display_id'] = info_dict['id']

        if info_dict.get('upload_date') is None and info_dict.get('timestamp') is not None:
            # Working around negative timestamps in Windows
            # (see http://bugs.python.org/issue1646728)
            if info_dict['timestamp'] < 0 and os.name == 'nt':
                info_dict['timestamp'] = 0
            upload_date = datetime.datetime.utcfromtimestamp(
                info_dict['timestamp'])
            info_dict['upload_date'] = upload_date.strftime('%Y%m%d')

        if self.params.get('listsubtitles', False):
            if 'automatic_captions' in info_dict:
                self.list_subtitles(info_dict['id'], info_dict.get('automatic_captions'), 'automatic captions')
            self.list_subtitles(info_dict['id'], info_dict.get('subtitles'), 'subtitles')
            return
        info_dict['requested_subtitles'] = self.process_subtitles(
            info_dict['id'], info_dict.get('subtitles'),
            info_dict.get('automatic_captions'))

        # This extractors handle format selection themselves
        if info_dict['extractor'] in ['Youku']:
            if download:
                self.process_info(info_dict)
            return info_dict

        # We now pick which formats have to be downloaded
        if info_dict.get('formats') is None:
            # There's only one format available
            formats = [info_dict]
        else:
            formats = info_dict['formats']

        if not formats:
            raise ExtractorError('No video formats found!')

        # We check that all the formats have the format and format_id fields
        for i, format in enumerate(formats):
            if 'url' not in format:
                raise ExtractorError('Missing "url" key in result (index %d)' % i)

            if format.get('format_id') is None:
                format['format_id'] = compat_str(i)
            if format.get('format') is None:
                format['format'] = '{id} - {res}{note}'.format(
                    id=format['format_id'],
                    res=self.format_resolution(format),
                    note=' ({0})'.format(format['format_note']) if format.get('format_note') is not None else '',
                )
            # Automatically determine file extension if missing
            if 'ext' not in format:
                format['ext'] = determine_ext(format['url']).lower()
            # Add HTTP headers, so that external programs can use them from the
            # json output
            full_format_info = info_dict.copy()
            full_format_info.update(format)
            format['http_headers'] = self._calc_headers(full_format_info)

        # TODO Central sorting goes here

        if formats[0] is not info_dict:
            # only set the 'formats' fields if the original info_dict list them
            # otherwise we end up with a circular reference, the first (and unique)
            # element in the 'formats' field in info_dict is info_dict itself,
            # wich can't be exported to json
            info_dict['formats'] = formats
        if self.params.get('listformats'):
            self.list_formats(info_dict)
            return
        if self.params.get('list_thumbnails'):
            self.list_thumbnails(info_dict)
            return

        req_format = self.params.get('format')
        if req_format is None:
            req_format_list = []
            if (self.params.get('outtmpl', DEFAULT_OUTTMPL) != '-' and
                    info_dict['extractor'] in ['youtube', 'ted']):
                merger = FFmpegMergerPP(self)
                if merger.available and merger.can_merge():
                    req_format_list.append('bestvideo+bestaudio')
            req_format_list.append('best')
            req_format = '/'.join(req_format_list)
        formats_to_download = []
        if req_format == 'all':
            formats_to_download = formats
        else:
            for rfstr in req_format.split(','):
                # We can accept formats requested in the format: 34/5/best, we pick
                # the first that is available, starting from left
                req_formats = rfstr.split('/')
                for rf in req_formats:
                    if re.match(r'.+?\+.+?', rf) is not None:
                        # Two formats have been requested like '137+139'
                        format_1, format_2 = rf.split('+')
                        formats_info = (self.select_format(format_1, formats),
                                        self.select_format(format_2, formats))
                        if all(formats_info):
                            # The first format must contain the video and the
                            # second the audio
                            if formats_info[0].get('vcodec') == 'none':
                                self.report_error('The first format must '
                                                  'contain the video, try using '
                                                  '"-f %s+%s"' % (format_2, format_1))
                                return
                            output_ext = (
                                formats_info[0]['ext']
                                if self.params.get('merge_output_format') is None
                                else self.params['merge_output_format'])
                            selected_format = {
                                'requested_formats': formats_info,
                                'format': '%s+%s' % (formats_info[0].get('format'),
                                                     formats_info[1].get('format')),
                                'format_id': '%s+%s' % (formats_info[0].get('format_id'),
                                                        formats_info[1].get('format_id')),
                                'width': formats_info[0].get('width'),
                                'height': formats_info[0].get('height'),
                                'resolution': formats_info[0].get('resolution'),
                                'fps': formats_info[0].get('fps'),
                                'vcodec': formats_info[0].get('vcodec'),
                                'vbr': formats_info[0].get('vbr'),
                                'stretched_ratio': formats_info[0].get('stretched_ratio'),
                                'acodec': formats_info[1].get('acodec'),
                                'abr': formats_info[1].get('abr'),
                                'ext': output_ext,
                            }
                        else:
                            selected_format = None
                    else:
                        selected_format = self.select_format(rf, formats)
                    if selected_format is not None:
                        formats_to_download.append(selected_format)
                        break
        if not formats_to_download:
            raise ExtractorError('requested format not available',
                                 expected=True)

        if download:
            if len(formats_to_download) > 1:
                self.to_screen('[info] %s: downloading video in %s formats' % (info_dict['id'], len(formats_to_download)))
            for format in formats_to_download:
                new_info = dict(info_dict)
                new_info.update(format)
                self.process_info(new_info)
        # We update the info dict with the best quality format (backwards compatibility)
        info_dict.update(formats_to_download[-1])
        return info_dict

    def process_subtitles(self, video_id, normal_subtitles, automatic_captions):
        """Select the requested subtitles and their format"""
        available_subs = {}
        if normal_subtitles and self.params.get('writesubtitles'):
            available_subs.update(normal_subtitles)
        if automatic_captions and self.params.get('writeautomaticsub'):
            for lang, cap_info in automatic_captions.items():
                if lang not in available_subs:
                    available_subs[lang] = cap_info

        if (not self.params.get('writesubtitles') and not
                self.params.get('writeautomaticsub') or not
                available_subs):
            return None

        if self.params.get('allsubtitles', False):
            requested_langs = available_subs.keys()
        else:
            if self.params.get('subtitleslangs', False):
                requested_langs = self.params.get('subtitleslangs')
            elif 'en' in available_subs:
                requested_langs = ['en']
            else:
                requested_langs = [list(available_subs.keys())[0]]

        formats_query = self.params.get('subtitlesformat', 'best')
        formats_preference = formats_query.split('/') if formats_query else []
        subs = {}
        for lang in requested_langs:
            formats = available_subs.get(lang)
            if formats is None:
                self.report_warning('%s subtitles not available for %s' % (lang, video_id))
                continue
            for ext in formats_preference:
                if ext == 'best':
                    f = formats[-1]
                    break
                matches = list(filter(lambda f: f['ext'] == ext, formats))
                if matches:
                    f = matches[-1]
                    break
            else:
                f = formats[-1]
                self.report_warning(
                    'No subtitle format found matching "%s" for language %s, '
                    'using %s' % (formats_query, lang, f['ext']))
            subs[lang] = f
        return subs

    def process_info(self, info_dict):
        """Process a single resolved IE result."""

        assert info_dict.get('_type', 'video') == 'video'

        max_downloads = self.params.get('max_downloads')
        if max_downloads is not None:
            if self._num_downloads >= int(max_downloads):
                raise MaxDownloadsReached()

        info_dict['fulltitle'] = info_dict['title']
        if len(info_dict['title']) > 200:
            info_dict['title'] = info_dict['title'][:197] + '...'

        if 'format' not in info_dict:
            info_dict['format'] = info_dict['ext']

        reason = self._match_entry(info_dict, incomplete=False)
        if reason is not None:
            self.to_screen('[download] ' + reason)
            return

        self._num_downloads += 1

        info_dict['_filename'] = filename = self.prepare_filename(info_dict)

        # Forced printings
        if self.params.get('forcetitle', False):
            self.to_stdout(info_dict['fulltitle'])
        if self.params.get('forceid', False):
            self.to_stdout(info_dict['id'])
        if self.params.get('forceurl', False):
            if info_dict.get('requested_formats') is not None:
                for f in info_dict['requested_formats']:
                    self.to_stdout(f['url'] + f.get('play_path', ''))
            else:
                # For RTMP URLs, also include the playpath
                self.to_stdout(info_dict['url'] + info_dict.get('play_path', ''))
        if self.params.get('forcethumbnail', False) and info_dict.get('thumbnail') is not None:
            self.to_stdout(info_dict['thumbnail'])
        if self.params.get('forcedescription', False) and info_dict.get('description') is not None:
            self.to_stdout(info_dict['description'])
        if self.params.get('forcefilename', False) and filename is not None:
            self.to_stdout(filename)
        if self.params.get('forceduration', False) and info_dict.get('duration') is not None:
            self.to_stdout(formatSeconds(info_dict['duration']))
        if self.params.get('forceformat', False):
            self.to_stdout(info_dict['format'])
        if self.params.get('forcejson', False):
            self.to_stdout(json.dumps(info_dict))

        # Do nothing else if in simulate mode
        if self.params.get('simulate', False):
            return

        if filename is None:
            return

        try:
            dn = os.path.dirname(sanitize_path(encodeFilename(filename)))
            if dn and not os.path.exists(dn):
                os.makedirs(dn)
        except (OSError, IOError) as err:
            self.report_error('unable to create directory ' + compat_str(err))
            return

        if self.params.get('writedescription', False):
            descfn = replace_extension(filename, 'description', info_dict.get('ext'))
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(descfn)):
                self.to_screen('[info] Video description is already present')
            elif info_dict.get('description') is None:
                self.report_warning('There\'s no description to write.')
            else:
                try:
                    self.to_screen('[info] Writing video description to: ' + descfn)
                    with io.open(encodeFilename(descfn), 'w', encoding='utf-8') as descfile:
                        descfile.write(info_dict['description'])
                except (OSError, IOError):
                    self.report_error('Cannot write description file ' + descfn)
                    return

        if self.params.get('writeannotations', False):
            annofn = replace_extension(filename, 'annotations.xml', info_dict.get('ext'))
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(annofn)):
                self.to_screen('[info] Video annotations are already present')
            else:
                try:
                    self.to_screen('[info] Writing video annotations to: ' + annofn)
                    with io.open(encodeFilename(annofn), 'w', encoding='utf-8') as annofile:
                        annofile.write(info_dict['annotations'])
                except (KeyError, TypeError):
                    self.report_warning('There are no annotations to write.')
                except (OSError, IOError):
                    self.report_error('Cannot write annotations file: ' + annofn)
                    return

        subtitles_are_requested = any([self.params.get('writesubtitles', False),
                                       self.params.get('writeautomaticsub')])

        if subtitles_are_requested and info_dict.get('requested_subtitles'):
            # subtitles download errors are already managed as troubles in relevant IE
            # that way it will silently go on when used with unsupporting IE
            subtitles = info_dict['requested_subtitles']
            ie = self.get_info_extractor(info_dict['extractor_key'])
            for sub_lang, sub_info in subtitles.items():
                sub_format = sub_info['ext']
                if sub_info.get('data') is not None:
                    sub_data = sub_info['data']
                else:
                    try:
                        sub_data = ie._download_webpage(
                            sub_info['url'], info_dict['id'], note=False)
                    except ExtractorError as err:
                        self.report_warning('Unable to download subtitle for "%s": %s' %
                                            (sub_lang, compat_str(err.cause)))
                        continue
                try:
                    sub_filename = subtitles_filename(filename, sub_lang, sub_format)
                    if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(sub_filename)):
                        self.to_screen('[info] Video subtitle %s.%s is already_present' % (sub_lang, sub_format))
                    else:
                        self.to_screen('[info] Writing video subtitles to: ' + sub_filename)
                        with io.open(encodeFilename(sub_filename), 'w', encoding='utf-8') as subfile:
                            subfile.write(sub_data)
                except (OSError, IOError):
                    self.report_error('Cannot write subtitles file ' + sub_filename)
                    return

        if self.params.get('writeinfojson', False):
            infofn = replace_extension(filename, 'info.json', info_dict.get('ext'))
            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(infofn)):
                self.to_screen('[info] Video description metadata is already present')
            else:
                self.to_screen('[info] Writing video description metadata as JSON to: ' + infofn)
                try:
                    write_json_file(self.filter_requested_info(info_dict), infofn)
                except (OSError, IOError):
                    self.report_error('Cannot write metadata to JSON file ' + infofn)
                    return

        self._write_thumbnails(info_dict, filename)

        if not self.params.get('skip_download', False):
            try:
                def dl(name, info):
                    fd = get_suitable_downloader(info, self.params)(self, self.params)
                    for ph in self._progress_hooks:
                        fd.add_progress_hook(ph)
                    if self.params.get('verbose'):
                        self.to_stdout('[debug] Invoking downloader on %r' % info.get('url'))
                    return fd.download(name, info)

                if info_dict.get('requested_formats') is not None:
                    downloaded = []
                    success = True
                    merger = FFmpegMergerPP(self)
                    if not merger.available:
                        postprocessors = []
                        self.report_warning('You have requested multiple '
                                            'formats but ffmpeg or avconv are not installed.'
                                            ' The formats won\'t be merged')
                    else:
                        postprocessors = [merger]

                    def compatible_formats(formats):
                        video, audio = formats
                        # Check extension
                        video_ext, audio_ext = audio.get('ext'), video.get('ext')
                        if video_ext and audio_ext:
                            COMPATIBLE_EXTS = (
                                ('mp3', 'mp4', 'm4a', 'm4p', 'm4b', 'm4r', 'm4v'),
                                ('webm')
                            )
                            for exts in COMPATIBLE_EXTS:
                                if video_ext in exts and audio_ext in exts:
                                    return True
                        # TODO: Check acodec/vcodec
                        return False

                    filename_real_ext = os.path.splitext(filename)[1][1:]
                    filename_wo_ext = (
                        os.path.splitext(filename)[0]
                        if filename_real_ext == info_dict['ext']
                        else filename)
                    requested_formats = info_dict['requested_formats']
                    if self.params.get('merge_output_format') is None and not compatible_formats(requested_formats):
                        info_dict['ext'] = 'mkv'
                        self.report_warning('You have requested formats incompatible for merge. '
                                            'The formats will be merged into mkv')
                    # Ensure filename always has a correct extension for successful merge
                    filename = '%s.%s' % (filename_wo_ext, info_dict['ext'])
                    if os.path.exists(encodeFilename(filename)):
                        self.to_screen(
                            '[download] %s has already been downloaded and '
                            'merged' % filename)
                    else:
                        for f in requested_formats:
                            new_info = dict(info_dict)
                            new_info.update(f)
                            fname = self.prepare_filename(new_info)
                            fname = prepend_extension(fname, 'f%s' % f['format_id'], new_info['ext'])
                            downloaded.append(fname)
                            partial_success = dl(fname, new_info)
                            success = success and partial_success
                        info_dict['__postprocessors'] = postprocessors
                        info_dict['__files_to_merge'] = downloaded
                else:
                    # Just a single file
                    success = dl(filename, info_dict)
            except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                self.report_error('unable to download video data: %s' % str(err))
                return
            except (OSError, IOError) as err:
                raise UnavailableVideoError(err)
            except (ContentTooShortError, ) as err:
                self.report_error('content too short (expected %s bytes and served %s)' % (err.expected, err.downloaded))
                return

            if success:
                # Fixup content
                fixup_policy = self.params.get('fixup')
                if fixup_policy is None:
                    fixup_policy = 'detect_or_warn'

                stretched_ratio = info_dict.get('stretched_ratio')
                if stretched_ratio is not None and stretched_ratio != 1:
                    if fixup_policy == 'warn':
                        self.report_warning('%s: Non-uniform pixel ratio (%s)' % (
                            info_dict['id'], stretched_ratio))
                    elif fixup_policy == 'detect_or_warn':
                        stretched_pp = FFmpegFixupStretchedPP(self)
                        if stretched_pp.available:
                            info_dict.setdefault('__postprocessors', [])
                            info_dict['__postprocessors'].append(stretched_pp)
                        else:
                            self.report_warning(
                                '%s: Non-uniform pixel ratio (%s). Install ffmpeg or avconv to fix this automatically.' % (
                                    info_dict['id'], stretched_ratio))
                    else:
                        assert fixup_policy in ('ignore', 'never')

                if info_dict.get('requested_formats') is None and info_dict.get('container') == 'm4a_dash':
                    if fixup_policy == 'warn':
                        self.report_warning('%s: writing DASH m4a. Only some players support this container.' % (
                            info_dict['id']))
                    elif fixup_policy == 'detect_or_warn':
                        fixup_pp = FFmpegFixupM4aPP(self)
                        if fixup_pp.available:
                            info_dict.setdefault('__postprocessors', [])
                            info_dict['__postprocessors'].append(fixup_pp)
                        else:
                            self.report_warning(
                                '%s: writing DASH m4a. Only some players support this container. Install ffmpeg or avconv to fix this automatically.' % (
                                    info_dict['id']))
                    else:
                        assert fixup_policy in ('ignore', 'never')

                try:
                    self.post_process(filename, info_dict)
                except (PostProcessingError) as err:
                    self.report_error('postprocessing: %s' % str(err))
                    return
                self.record_download_archive(info_dict)

    def download(self, url_list):
        """Download a given list of URLs."""
        outtmpl = self.params.get('outtmpl', DEFAULT_OUTTMPL)
        if (len(url_list) > 1 and
                '%' not in outtmpl and
                self.params.get('max_downloads') != 1):
            raise SameFileError(outtmpl)

        for url in url_list:
            try:
                # It also downloads the videos
                res = self.extract_info(url)
            except UnavailableVideoError:
                self.report_error('unable to download video')
            except MaxDownloadsReached:
                self.to_screen('[info] Maximum number of downloaded files reached.')
                raise
            else:
                if self.params.get('dump_single_json', False):
                    self.to_stdout(json.dumps(res))

        return self._download_retcode

    def download_with_info_file(self, info_filename):
        with contextlib.closing(fileinput.FileInput(
                [info_filename], mode='r',
                openhook=fileinput.hook_encoded('utf-8'))) as f:
            # FileInput doesn't have a read method, we can't call json.load
            info = self.filter_requested_info(json.loads('\n'.join(f)))
        try:
            self.process_ie_result(info, download=True)
        except DownloadError:
            webpage_url = info.get('webpage_url')
            if webpage_url is not None:
                self.report_warning('The info failed to download, trying with "%s"' % webpage_url)
                return self.download([webpage_url])
            else:
                raise
        return self._download_retcode

    @staticmethod
    def filter_requested_info(info_dict):
        return dict(
            (k, v) for k, v in info_dict.items()
            if k not in ['requested_formats', 'requested_subtitles'])

    def post_process(self, filename, ie_info):
        """Run all the postprocessors on the given file."""
        info = dict(ie_info)
        info['filepath'] = filename
        pps_chain = []
        if ie_info.get('__postprocessors') is not None:
            pps_chain.extend(ie_info['__postprocessors'])
        pps_chain.extend(self._pps)
        for pp in pps_chain:
            try:
                files_to_delete, info = pp.run(info)
            except PostProcessingError as e:
                self.report_error(e.msg)
            if files_to_delete and not self.params.get('keepvideo', False):
                for old_filename in files_to_delete:
                    self.to_screen('Deleting original file %s (pass -k to keep)' % old_filename)
                    try:
                        os.remove(encodeFilename(old_filename))
                    except (IOError, OSError):
                        self.report_warning('Unable to remove downloaded original file')

    def _make_archive_id(self, info_dict):
        # Future-proof against any change in case
        # and backwards compatibility with prior versions
        extractor = info_dict.get('extractor_key')
        if extractor is None:
            if 'id' in info_dict:
                extractor = info_dict.get('ie_key')  # key in a playlist
        if extractor is None:
            return None  # Incomplete video information
        return extractor.lower() + ' ' + info_dict['id']

    def in_download_archive(self, info_dict):
        fn = self.params.get('download_archive')
        if fn is None:
            return False

        vid_id = self._make_archive_id(info_dict)
        if vid_id is None:
            return False  # Incomplete video information

        try:
            with locked_file(fn, 'r', encoding='utf-8') as archive_file:
                for line in archive_file:
                    if line.strip() == vid_id:
                        return True
        except IOError as ioe:
            if ioe.errno != errno.ENOENT:
                raise
        return False

    def record_download_archive(self, info_dict):
        fn = self.params.get('download_archive')
        if fn is None:
            return
        vid_id = self._make_archive_id(info_dict)
        assert vid_id
        with locked_file(fn, 'a', encoding='utf-8') as archive_file:
            archive_file.write(vid_id + '\n')

    @staticmethod
    def format_resolution(format, default='unknown'):
        if format.get('vcodec') == 'none':
            return 'audio only'
        if format.get('resolution') is not None:
            return format['resolution']
        if format.get('height') is not None:
            if format.get('width') is not None:
                res = '%sx%s' % (format['width'], format['height'])
            else:
                res = '%sp' % format['height']
        elif format.get('width') is not None:
            res = '?x%d' % format['width']
        else:
            res = default
        return res

    def _format_note(self, fdict):
        res = ''
        if fdict.get('ext') in ['f4f', 'f4m']:
            res += '(unsupported) '
        if fdict.get('format_note') is not None:
            res += fdict['format_note'] + ' '
        if fdict.get('tbr') is not None:
            res += '%4dk ' % fdict['tbr']
        if fdict.get('container') is not None:
            if res:
                res += ', '
            res += '%s container' % fdict['container']
        if (fdict.get('vcodec') is not None and
                fdict.get('vcodec') != 'none'):
            if res:
                res += ', '
            res += fdict['vcodec']
            if fdict.get('vbr') is not None:
                res += '@'
        elif fdict.get('vbr') is not None and fdict.get('abr') is not None:
            res += 'video@'
        if fdict.get('vbr') is not None:
            res += '%4dk' % fdict['vbr']
        if fdict.get('fps') is not None:
            res += ', %sfps' % fdict['fps']
        if fdict.get('acodec') is not None:
            if res:
                res += ', '
            if fdict['acodec'] == 'none':
                res += 'video only'
            else:
                res += '%-5s' % fdict['acodec']
        elif fdict.get('abr') is not None:
            if res:
                res += ', '
            res += 'audio'
        if fdict.get('abr') is not None:
            res += '@%3dk' % fdict['abr']
        if fdict.get('asr') is not None:
            res += ' (%5dHz)' % fdict['asr']
        if fdict.get('filesize') is not None:
            if res:
                res += ', '
            res += format_bytes(fdict['filesize'])
        elif fdict.get('filesize_approx') is not None:
            if res:
                res += ', '
            res += '~' + format_bytes(fdict['filesize_approx'])
        return res

    def list_formats(self, info_dict):
        formats = info_dict.get('formats', [info_dict])
        table = [
            [f['format_id'], f['ext'], self.format_resolution(f), self._format_note(f)]
            for f in formats
            if f.get('preference') is None or f['preference'] >= -1000]
        if len(formats) > 1:
            table[-1][-1] += (' ' if table[-1][-1] else '') + '(best)'

        header_line = ['format code', 'extension', 'resolution', 'note']
        self.to_screen(
            '[info] Available formats for %s:\n%s' %
            (info_dict['id'], render_table(header_line, table)))

    def list_thumbnails(self, info_dict):
        thumbnails = info_dict.get('thumbnails')
        if not thumbnails:
            tn_url = info_dict.get('thumbnail')
            if tn_url:
                thumbnails = [{'id': '0', 'url': tn_url}]
            else:
                self.to_screen(
                    '[info] No thumbnails present for %s' % info_dict['id'])
                return

        self.to_screen(
            '[info] Thumbnails for %s:' % info_dict['id'])
        self.to_screen(render_table(
            ['ID', 'width', 'height', 'URL'],
            [[t['id'], t.get('width', 'unknown'), t.get('height', 'unknown'), t['url']] for t in thumbnails]))

    def list_subtitles(self, video_id, subtitles, name='subtitles'):
        if not subtitles:
            self.to_screen('%s has no %s' % (video_id, name))
            return
        self.to_screen(
            'Available %s for %s:' % (name, video_id))
        self.to_screen(render_table(
            ['Language', 'formats'],
            [[lang, ', '.join(f['ext'] for f in reversed(formats))]
                for lang, formats in subtitles.items()]))

    def urlopen(self, req):
        """ Start an HTTP download """

        # According to RFC 3986, URLs can not contain non-ASCII characters, however this is not
        # always respected by websites, some tend to give out URLs with non percent-encoded
        # non-ASCII characters (see telemb.py, ard.py [#3412])
        # urllib chokes on URLs with non-ASCII characters (see http://bugs.python.org/issue3991)
        # To work around aforementioned issue we will replace request's original URL with
        # percent-encoded one
        req_is_string = isinstance(req, compat_basestring)
        url = req if req_is_string else req.get_full_url()
        url_escaped = escape_url(url)

        # Substitute URL if any change after escaping
        if url != url_escaped:
            if req_is_string:
                req = url_escaped
            else:
                req = compat_urllib_request.Request(
                    url_escaped, data=req.data, headers=req.headers,
                    origin_req_host=req.origin_req_host, unverifiable=req.unverifiable)

        return self._opener.open(req, timeout=self._socket_timeout)

    def print_debug_header(self):
        if not self.params.get('verbose'):
            return

        if type('') is not compat_str:
            # Python 2.6 on SLES11 SP1 (https://github.com/rg3/youtube-dl/issues/3326)
            self.report_warning(
                'Your Python is broken! Update to a newer and supported version')

        stdout_encoding = getattr(
            sys.stdout, 'encoding', 'missing (%s)' % type(sys.stdout).__name__)
        encoding_str = (
            '[debug] Encodings: locale %s, fs %s, out %s, pref %s\n' % (
                locale.getpreferredencoding(),
                sys.getfilesystemencoding(),
                stdout_encoding,
                self.get_encoding()))
        write_string(encoding_str, encoding=None)

        self._write_string('[debug] youtube-dl version ' + __version__ + '\n')
        try:
            sp = subprocess.Popen(
                ['git', 'rev-parse', '--short', 'HEAD'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.abspath(__file__)))
            out, err = sp.communicate()
            out = out.decode().strip()
            if re.match('[0-9a-f]+', out):
                self._write_string('[debug] Git HEAD: ' + out + '\n')
        except Exception:
            try:
                sys.exc_clear()
            except Exception:
                pass
        self._write_string('[debug] Python version %s - %s\n' % (
            platform.python_version(), platform_name()))

        exe_versions = FFmpegPostProcessor.get_versions(self)
        exe_versions['rtmpdump'] = rtmpdump_version()
        exe_str = ', '.join(
            '%s %s' % (exe, v)
            for exe, v in sorted(exe_versions.items())
            if v
        )
        if not exe_str:
            exe_str = 'none'
        self._write_string('[debug] exe versions: %s\n' % exe_str)

        proxy_map = {}
        for handler in self._opener.handlers:
            if hasattr(handler, 'proxies'):
                proxy_map.update(handler.proxies)
        self._write_string('[debug] Proxy map: ' + compat_str(proxy_map) + '\n')

        if self.params.get('call_home', False):
            ipaddr = self.urlopen('https://yt-dl.org/ip').read().decode('utf-8')
            self._write_string('[debug] Public IP address: %s\n' % ipaddr)
            latest_version = self.urlopen(
                'https://yt-dl.org/latest/version').read().decode('utf-8')
            if version_tuple(latest_version) > version_tuple(__version__):
                self.report_warning(
                    'You are using an outdated version (newest version: %s)! '
                    'See https://yt-dl.org/update if you need help updating.' %
                    latest_version)

    def _setup_opener(self):
        timeout_val = self.params.get('socket_timeout')
        self._socket_timeout = 600 if timeout_val is None else float(timeout_val)

        opts_cookiefile = self.params.get('cookiefile')
        opts_proxy = self.params.get('proxy')

        if opts_cookiefile is None:
            self.cookiejar = compat_cookiejar.CookieJar()
        else:
            self.cookiejar = compat_cookiejar.MozillaCookieJar(
                opts_cookiefile)
            if os.access(opts_cookiefile, os.R_OK):
                self.cookiejar.load()

        cookie_processor = compat_urllib_request.HTTPCookieProcessor(
            self.cookiejar)
        if opts_proxy is not None:
            if opts_proxy == '':
                proxies = {}
            else:
                proxies = {'http': opts_proxy, 'https': opts_proxy}
        else:
            proxies = compat_urllib_request.getproxies()
            # Set HTTPS proxy to HTTP one if given (https://github.com/rg3/youtube-dl/issues/805)
            if 'http' in proxies and 'https' not in proxies:
                proxies['https'] = proxies['http']
        proxy_handler = PerRequestProxyHandler(proxies)

        debuglevel = 1 if self.params.get('debug_printtraffic') else 0
        https_handler = make_HTTPS_handler(self.params, debuglevel=debuglevel)
        ydlh = YoutubeDLHandler(self.params, debuglevel=debuglevel)
        opener = compat_urllib_request.build_opener(
            proxy_handler, https_handler, cookie_processor, ydlh)

        # Delete the default user-agent header, which would otherwise apply in
        # cases where our custom HTTP handler doesn't come into play
        # (See https://github.com/rg3/youtube-dl/issues/1309 for details)
        opener.addheaders = []
        self._opener = opener

    def encode(self, s):
        if isinstance(s, bytes):
            return s  # Already encoded

        try:
            return s.encode(self.get_encoding())
        except UnicodeEncodeError as err:
            err.reason = err.reason + '. Check your system encoding configuration or use the --encoding option.'
            raise

    def get_encoding(self):
        encoding = self.params.get('encoding')
        if encoding is None:
            encoding = preferredencoding()
        return encoding

    def _write_thumbnails(self, info_dict, filename):
        if self.params.get('writethumbnail', False):
            thumbnails = info_dict.get('thumbnails')
            if thumbnails:
                thumbnails = [thumbnails[-1]]
        elif self.params.get('write_all_thumbnails', False):
            thumbnails = info_dict.get('thumbnails')
        else:
            return

        if not thumbnails:
            # No thumbnails present, so return immediately
            return

        for t in thumbnails:
            thumb_ext = determine_ext(t['url'], 'jpg')
            suffix = '_%s' % t['id'] if len(thumbnails) > 1 else ''
            thumb_display_id = '%s ' % t['id'] if len(thumbnails) > 1 else ''
            t['filename'] = thumb_filename = os.path.splitext(filename)[0] + suffix + '.' + thumb_ext

            if self.params.get('nooverwrites', False) and os.path.exists(encodeFilename(thumb_filename)):
                self.to_screen('[%s] %s: Thumbnail %sis already present' %
                               (info_dict['extractor'], info_dict['id'], thumb_display_id))
            else:
                self.to_screen('[%s] %s: Downloading thumbnail %s...' %
                               (info_dict['extractor'], info_dict['id'], thumb_display_id))
                try:
                    uf = self.urlopen(t['url'])
                    with open(thumb_filename, 'wb') as thumbf:
                        shutil.copyfileobj(uf, thumbf)
                    self.to_screen('[%s] %s: Writing thumbnail %sto: %s' %
                                   (info_dict['extractor'], info_dict['id'], thumb_display_id, thumb_filename))
                except (compat_urllib_error.URLError, compat_http_client.HTTPException, socket.error) as err:
                    self.report_warning('Unable to download thumbnail "%s": %s' %
                                        (t['url'], compat_str(err)))
