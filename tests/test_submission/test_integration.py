import csv
import logging
import os
from datetime import datetime

from brainscore.submission.database import connect_db
from brainscore.submission.evaluation import run_evaluation
from brainscore.submission.models import Score, Model, Submission
from tests.test_submission.test_db import clear_schema, init_user

logger = logging.getLogger(__name__)


class TestIntegration:

    @classmethod
    def setup_class(cls):
        logger.info('Connect to database')
        connect_db('brainscore-ohio-test')
        clear_schema()

    def setup_method(self):
        logger.info('Initialize database')
        init_user()

    def teardown_method(self):
        # os.rmdir(self.working_dir)
        logger.info('Clean database')
        clear_schema()

    def test_evaluation(self, tmpdir):
        working_dir = str(tmpdir.mkdir('sub'))
        config_dir = str(os.path.join(os.path.dirname(__file__), 'configs/'))
        run_evaluation(config_dir, working_dir, 33, 'brainscore-ohio-test', models=['alexnet'],
                       benchmarks=['dicarlo.Majaj2015.IT-pls'])
        with open('result_33.csv') as results:
            csv_reader = csv.reader(results, delimiter=',')
            next(csv_reader)  # header row
            result_row = next(csv_reader)
            # alexnet,dicarlo.Majaj2015.IT-pls,0.5857491098187586,0.5079816726934638,0.003155449372125895
            assert result_row[0] == 'alexnet'
            assert result_row[1] == 'dicarlo.Majaj2015.IT-pls'
            assert result_row[2] == '0.5857491098187586'
            assert result_row[3] == '0.5079816726934638'
            assert result_row[4] == '0.003155449372125895'
        scores = Score.select()
        assert len(scores) == 1
        assert scores[
                   0].comment is None  # If comment is none the score was successfully stored, otherwise there would be an error message there

    def test_rerun_evaluation(self, tmpdir):
        working_dir = str(tmpdir.mkdir('sub'))
        config_dir = str(os.path.join(os.path.dirname(__file__), 'configs/'))
        submission = Submission.create(id=33, submitter=1, timestamp=datetime.now(),
                                       model_type='BaseModel', status='running')
        model = Model.create(name='alexnet', owner=submission.submitter, public=False,
                             submission=submission)
        with open(f'{config_dir}submission_34.json', 'w') as rerun:
            rerun.write(f"""{{
            "model_ids": [{model.id}], "user_id": 1}}""")
        run_evaluation(config_dir, working_dir, 34, 'brainscore-ohio-test',
                       benchmarks=['dicarlo.Rajalingham2018-i2n'])
        with open('result_34.csv') as results:
            csv_reader = csv.reader(results, delimiter=',')
            next(csv_reader)  # header row
            result_row = next(csv_reader)
            # alexnet,dicarlo.Majaj2015.IT-pls,0.5857491098187586,0.5079816726934638,0.003155449372125895
            assert result_row[0] == 'alexnet'
            assert result_row[1] == 'dicarlo.Majaj2015.IT-pls'
            assert result_row[2] == '0.5857491098187586'
            assert result_row[3] == '0.5079816726934638'
            assert result_row[4] == '0.003155449372125895'

    def test_failure_evaluation(self, tmpdir):
        working_dir = str(tmpdir.mkdir('sub'))
        config_dir = str(os.path.join(os.path.dirname(__file__), 'configs/'))
        exception = False
        try:
            run_evaluation(config_dir, working_dir, 35, 'brainscore-ohio-test', models=['alexnet'],
                       benchmarks=['dicarlo.Rajalingham2018-i2n'])
        except:
            exception = True
        assert exception



    def test_model_failure_evaluation(self, tmpdir):
        working_dir = str(tmpdir.mkdir('sub'))
        config_dir = str(os.path.join(os.path.dirname(__file__), 'configs/'))
        run_evaluation(config_dir, working_dir, 36, 'brainscore-ohio-test', models=['alexnet'],
                       benchmarks=['movshon.FreemanZiemba2013.V1-pls'])
        with open('result_36.csv') as results:
            csv_reader = csv.reader(results, delimiter=',')
            next(csv_reader)  # header row
            result_row = next(csv_reader)
            assert result_row[0] == 'alexnet'
            assert result_row[1] == 'movshon.FreemanZiemba2013.V1-pls'
            assert result_row[2] == '0.0'
            assert result_row[3] == '0.0'
        model = Model.get(submission=Submission.get(id=36))[0]
        score = Score.get(model=model)[0]
        assert score.comment is not None  # When there's a problem, the comment field contains an error message