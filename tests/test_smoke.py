import os, sys, unittest, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hexgen.dice import Dice
from hexgen.tables import Registry, parse_label
from hexgen import campaign, render

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')


class Smoke(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(parse_label('02–03', 100), (2, 3))
        self.assertEqual(parse_label('00', 100), (100, 100))
        self.assertEqual(parse_label('97–00', 100), (97, 100))
        self.assertEqual(parse_label('8–0', 10), (8, 10))

    def test_every_table_rolls(self):
        R = Registry(DATA, Dice(1))
        for t in R.tables:
            for _ in range(5):
                R.roll(t)

    def test_same_seed_same_region(self):
        a = campaign.build(Registry(DATA, Dice(9)), 10, 8, 'sd')
        b = campaign.build(Registry(DATA, Dice(9)), 10, 8, 'sd')
        self.assertEqual([h.terrain for h in a['map']], [h.terrain for h in b['map']])
        self.assertEqual(a['name'], b['name'])

    def test_both_systems_render(self):
        for system in ('sd', 'ose'):
            R = Registry(DATA, Dice(4))
            reg = campaign.build(R, 12, 9, system, sea='ws')
            self.assertTrue(reg['settlements'])
            with tempfile.TemporaryDirectory() as d:
                render.write_html(R, reg, os.path.join(d, 'x.html'))
                render.write_md(reg, os.path.join(d, 'x.md'))
                render.write_json(reg, os.path.join(d, 'x.json'))


if __name__ == '__main__':
    unittest.main()
