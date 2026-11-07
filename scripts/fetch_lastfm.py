#!/usr/bin/env python3
"""Publish a small credential-free Last.fm snapshot; retain cached data on error."""
import datetime
import json
import os
from pathlib import Path
import urllib.parse
import urllib.request

OUTPUT = Path('assets/data/lastfm.json')


def normalize(payload):
    recent = payload.get('recenttracks')
    if not isinstance(recent, dict):
        raise ValueError('Invalid Last.fm response')
    raw = recent.get('track', [])
    if isinstance(raw, dict):
        raw = [raw]
    tracks = []
    for item in raw[:8]:
        images = item.get('image', [])
        image = next((img.get('#text') for img in reversed(images) if img.get('#text')), '')
        # Last.fm's standard empty artwork placeholder is not useful.
        if '2a96cbd8b46e442fc41c2b86b821562f' in image:
            image = ''
        tracks.append({
            'name': item.get('name', ''),
            'artist': item.get('artist', {}).get('#text', ''),
            'album': item.get('album', {}).get('#text', ''),
            'url': item.get('url', ''),
            'image': image,
            'now_playing': item.get('@attr', {}).get('nowplaying') == 'true',
            'played_at': item.get('date', {}).get('uts'),
        })
    return {'updated_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'tracks': tracks}


def main():
    username = os.environ.get('LASTFM_USERNAME', '').strip()
    key = os.environ.get('LASTFM_API_KEY', '').strip()
    if not username or not key:
        print('Last.fm not configured; keeping the fallback/cached snapshot.')
        return
    query = urllib.parse.urlencode({
        'method': 'user.getRecentTracks', 'user': username,
        'api_key': key, 'format': 'json', 'limit': 8,
    })
    request = urllib.request.Request('https://ws.audioscrobbler.com/2.0/?' + query,
                                     headers={'User-Agent': 'BudihalLogs/1.0'})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = normalize(json.load(response))
        temporary = OUTPUT.with_suffix('.tmp')
        temporary.write_text(json.dumps(data, ensure_ascii=False) + '\n')
        temporary.replace(OUTPUT)
        print('Last.fm snapshot updated.')
    except Exception:
        # Never log request URLs or exceptions that could include the API key.
        print('Last.fm unavailable; retaining the previous snapshot.')


if __name__ == '__main__':
    main()
