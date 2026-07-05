#!/usr/bin/env python

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import cli
from utils.db import create_article_db
from utils.sentiment import SentimentJudgeError


def _article(url, published_at, title='Trump does something', description='A story about Donald Trump.', source='Example News'):
    return {
        'url': url,
        'published_at': published_at,
        'title': title,
        'description': description,
        'source': source,
        'category': 'politics',
        'author': 'Jane Reporter',
    }


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / 'articles.duckdb')


@pytest.fixture
def seeded_db(db_path):
    """A DB with one recent DJT article, one recent non-DJT article, and one stale DJT article."""
    db = create_article_db(db_path)
    db.insert_articles(
        [
            _article('https://example.com/recent-djt', '2026-07-01 10:00', title='Trump Faces New Investigation'),
            _article(
                'https://example.com/recent-other',
                '2026-07-01 10:05',
                title='Local Bakery Wins Award',
                description='A bakery in town won a pie contest.',
            ),
            _article('https://example.com/stale-djt', '2026-06-01 10:00', title='Trump Rally Draws Crowd'),
        ]
    )
    db.close()
    return db_path


class TestTargetConfig:
    def test_known_targets_resolve(self):
        assert cli._target_config('local')['model']
        assert cli._target_config('remote')['model']

    def test_unknown_target_raises_system_exit(self):
        with pytest.raises(SystemExit):
            cli._target_config('bogus')


class TestRecentArticles:
    def test_filters_by_published_at_cutoff(self, seeded_db):
        db = create_article_db(seeded_db)
        try:
            recent = cli._recent_articles(db, hours=8760)  # ~1 year, both should be in range relative to 2026-07-01
        finally:
            db.close()
        urls = {a['url'] for a in recent}
        assert 'https://example.com/recent-djt' in urls
        assert 'https://example.com/recent-other' in urls


class TestLoadDjtArticles:
    def test_filters_to_djt_related_only(self, seeded_db):
        articles = cli._load_djt_articles(seeded_db, hours=999999)
        titles = {a['title'] for a in articles}
        assert 'Local Bakery Wins Award' not in titles
        assert any('Trump' in t for t in titles)

    def test_limit_truncates_results(self, seeded_db):
        articles = cli._load_djt_articles(seeded_db, hours=999999, limit=1)
        assert len(articles) == 1


class TestCmdArticles:
    def test_prints_recent_articles(self, seeded_db, capsys):
        args = cli.build_parser().parse_args(['--articles', '--db', seeded_db, '--hours', '999999'])
        cli.cmd_articles(args)
        out = capsys.readouterr().out
        assert 'Trump Faces New Investigation' in out
        assert 'Local Bakery Wins Award' in out

    def test_djt_only_flag_excludes_non_djt(self, seeded_db, capsys):
        args = cli.build_parser().parse_args(['--articles', '--db', seeded_db, '--hours', '999999', '--djt-only'])
        cli.cmd_articles(args)
        out = capsys.readouterr().out
        assert 'Trump Faces New Investigation' in out
        assert 'Local Bakery Wins Award' not in out


class TestCmdJudge:
    @patch('cli.score_articles')
    def test_labels_keep_and_drop_by_threshold(self, mock_score, seeded_db, capsys):
        mock_score.return_value = {0: -0.8, 1: 0.5}
        args = cli.build_parser().parse_args(['--judge', '--target', 'local', '--db', seeded_db, '--hours', '999999'])

        rc = cli.cmd_judge(args)

        out = capsys.readouterr().out
        assert rc == 0
        assert 'keep' in out
        assert 'drop' in out

    @patch('cli.score_articles')
    def test_model_override_reaches_score_articles(self, mock_score, seeded_db, capsys):
        mock_score.return_value = {0: -0.8, 1: -0.8}
        args = cli.build_parser().parse_args(
            [
                '--judge',
                '--target',
                'remote',
                '--model',
                'accounts/fireworks/models/minimax-m3',
                '--db',
                seeded_db,
                '--hours',
                '999999',
            ]
        )

        cli.cmd_judge(args)

        assert mock_score.call_args.kwargs['model'] == 'accounts/fireworks/models/minimax-m3'

    @patch('cli.score_articles')
    def test_no_model_override_keeps_target_default(self, mock_score, seeded_db, capsys):
        mock_score.return_value = {0: -0.8, 1: -0.8}
        args = cli.build_parser().parse_args(['--judge', '--target', 'remote', '--db', seeded_db, '--hours', '999999'])

        cli.cmd_judge(args)

        assert mock_score.call_args.kwargs['model'] == cli.TARGETS['remote']['model']

    @patch('cli.score_articles')
    def test_judge_call_failure_returns_nonzero(self, mock_score, seeded_db, capsys):
        mock_score.side_effect = SentimentJudgeError("boom")
        args = cli.build_parser().parse_args(['--judge', '--target', 'remote', '--db', seeded_db, '--hours', '999999'])

        rc = cli.cmd_judge(args)

        assert rc == 1
        assert 'boom' in capsys.readouterr().out

    def test_no_articles_in_range_is_a_noop(self, seeded_db, capsys):
        args = cli.build_parser().parse_args(['--judge', '--target', 'local', '--db', seeded_db, '--hours', '0'])

        rc = cli.cmd_judge(args)

        assert rc == 0
        assert 'No DJT-related articles' in capsys.readouterr().out


class TestCmdCompare:
    @patch('cli.score_articles')
    def test_reports_deltas_and_disagreements(self, mock_score, seeded_db, capsys):
        # local scores everything very negative, remote scores everything positive -> full disagreement
        def fake_score(articles, **kwargs):
            return (
                {i: -0.9 for i in range(len(articles))}
                if kwargs.get('model') == cli.TARGETS['local']['model']
                else {i: 0.9 for i in range(len(articles))}
            )

        mock_score.side_effect = fake_score
        args = cli.build_parser().parse_args(['--compare', '--db', seeded_db, '--hours', '999999'])

        rc = cli.cmd_compare(args)

        out = capsys.readouterr().out
        assert rc == 0
        assert 'disagreements=' in out

    @patch('cli.score_articles')
    def test_one_target_failing_returns_nonzero(self, mock_score, seeded_db, capsys):
        def fake_score(articles, **kwargs):
            if kwargs.get('model') == cli.TARGETS['local']['model']:
                raise SentimentJudgeError("local down")
            return {i: 0.1 for i in range(len(articles))}

        mock_score.side_effect = fake_score
        args = cli.build_parser().parse_args(['--compare', '--db', seeded_db, '--hours', '999999'])

        rc = cli.cmd_compare(args)

        assert rc == 1
        assert 'local down' in capsys.readouterr().out


class TestCmdHealth:
    @patch('cli.score_articles')
    def test_success_reports_ok(self, mock_score, capsys):
        mock_score.return_value = {0: -0.5, 1: 0.5}
        args = cli.build_parser().parse_args(['--health', '--target', 'remote'])

        rc = cli.cmd_health(args)

        assert rc == 0
        assert 'OK' in capsys.readouterr().out

    @patch('cli.score_articles')
    def test_failure_reports_error(self, mock_score, capsys):
        mock_score.side_effect = SentimentJudgeError("no route to host")

        args = cli.build_parser().parse_args(['--health', '--target', 'remote'])
        rc = cli.cmd_health(args)

        assert rc == 1
        assert 'no route to host' in capsys.readouterr().out

    @patch('cli.score_articles')
    def test_model_override_reaches_score_articles(self, mock_score, capsys):
        mock_score.return_value = {0: -0.5, 1: 0.5}
        args = cli.build_parser().parse_args(
            ['--health', '--target', 'remote', '--model', 'accounts/fireworks/models/minimax-m3']
        )

        cli.cmd_health(args)

        assert mock_score.call_args.kwargs['model'] == 'accounts/fireworks/models/minimax-m3'

    @patch('cli.requests.get')
    @patch('cli.score_articles')
    def test_local_target_checks_model_status(self, mock_score, mock_get, capsys):
        mock_score.return_value = {0: -0.5, 1: 0.5}
        status_response = Mock()
        status_response.raise_for_status = Mock()
        status_response.json.return_value = {'models': [{'id': cli.TARGETS['local']['model'], 'loaded': True}]}
        mock_get.return_value = status_response

        args = cli.build_parser().parse_args(['--health', '--target', 'local'])
        rc = cli.cmd_health(args)

        assert rc == 0
        mock_get.assert_called_once()
