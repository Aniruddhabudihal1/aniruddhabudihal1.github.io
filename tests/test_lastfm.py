import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('lastfm', Path(__file__).parents[1] / 'scripts/fetch_lastfm.py')
lastfm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lastfm)


class LastfmTests(unittest.TestCase):
    def test_now_playing_and_missing_artwork(self):
        data = lastfm.normalize({'recenttracks': {'track': [{
            'name': 'Test song', 'artist': {'#text': 'Test artist'},
            '@attr': {'nowplaying': 'true'},
        }]}})
        self.assertTrue(data['tracks'][0]['now_playing'])
        self.assertEqual(data['tracks'][0]['image'], '')
        self.assertNotIn('api_key', json.dumps(data))

    def test_single_track_response(self):
        track = lastfm.normalize({'recenttracks': {'track': {'date': {'uts': '123'}}}})['tracks'][0]
        self.assertFalse(track['now_playing'])
        self.assertEqual(track['played_at'], '123')

    def test_api_error(self):
        with self.assertRaises(ValueError):
            lastfm.normalize({'error': 6, 'message': 'User not found'})

    def test_request_failure_keeps_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'lastfm.json'
            output.write_text('cached')
            with patch.object(lastfm, 'OUTPUT', output), patch.dict(os.environ, {
                'LASTFM_USERNAME': 'test', 'LASTFM_API_KEY': 'not-a-real-key',
            }), patch('urllib.request.urlopen', side_effect=OSError('offline')):
                lastfm.main()
            self.assertEqual(output.read_text(), 'cached')

    def test_success_writes_public_snapshot_only(self):
        payload = {'recenttracks': {'track': [{'name': 'Fixture', 'artist': {'#text': 'Artist'}}]}}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'lastfm.json'
            with patch.object(lastfm, 'OUTPUT', output), patch.dict(os.environ, {
                'LASTFM_USERNAME': 'test', 'LASTFM_API_KEY': 'not-a-real-key',
            }), patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(payload).encode())):
                lastfm.main()
            snapshot = output.read_text()
            self.assertEqual(json.loads(snapshot)['tracks'][0]['name'], 'Fixture')
            self.assertNotIn('not-a-real-key', snapshot)
            self.assertNotIn('api_key', snapshot)

    def test_unconfigured_makes_no_request(self):
        with patch.dict(os.environ, {'LASTFM_USERNAME': '', 'LASTFM_API_KEY': ''}), patch('urllib.request.urlopen') as request:
            lastfm.main()
            request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
