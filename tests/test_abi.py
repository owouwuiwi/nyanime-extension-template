import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from check_abi import verify, read_classes


class AbiTest(unittest.TestCase):
    def test_custom_families_require_their_own_host_contracts(self):
        for family in ['news', 'tv', 'addon']:
            source = {'name': 'example/Factory', 'parents': [], 'refs': [], 'types': ['nyanime/'+family+'/api/Contract']}
            self.assertTrue(verify([source], []))

    def test_inherited_members_are_resolved(self):
        parent = 'eu/kanade/tachiyomi/source/Base'
        child = 'eu/kanade/tachiyomi/source/Derived'
        source = {'name': 'example/Source', 'parents': [child], 'refs': [(child, 'method', 'open', '()V')]}
        baseline = [{'name': parent, 'parents': [], 'members': {('method', 'open', '()V')}},
                    {'name': child, 'parents': [parent], 'members': set()}]
        self.assertEqual([], verify([source], baseline))

    def test_host_only_type_is_not_accepted_in_base_source(self):
        source = {'name': 'example/Source', 'parents': [],
                  'refs': [('eu/kanade/tachiyomi/source/model/OptionalData', 'method', 'value', '()V')]}
        self.assertEqual(1, len(verify([source], [])))

    def test_optional_namespace_is_separate(self):
        source = {'name': 'example/optional/Factory', 'parents': ['nyanime/extension/api/SourceCapabilitiesFactory'], 'refs': []}
        self.assertEqual([], verify([source], [], ['example/optional/']))
        self.assertEqual(1, len(verify([source], [])))

    def test_changed_method_descriptor_is_rejected(self):
        owner = 'eu/kanade/tachiyomi/source/Base'
        source = {'name': 'example/Source', 'parents': [], 'refs': [(owner, 'method', 'open', '(I)V')]}
        self.assertEqual(1, len(verify([source], [{'name': owner, 'parents': [], 'members': {('method', 'open', '()V')}}])))

    def test_host_only_type_in_a_field_descriptor_is_rejected(self):
        source = {'name': 'example/Source', 'parents': [], 'refs': [],
                  'types': ['eu/kanade/tachiyomi/source/model/OptionalData']}
        self.assertEqual(1, len(verify([source], [])))

    def test_pinned_profiles_contain_expected_public_contracts(self):
        sdk = Path(__file__).resolve().parents[1] / 'sdk'
        video = {item['name']: item for item in read_classes(sdk / 'aniyomi-video-api.jar')}
        manga = {item['name']: item for item in read_classes(sdk / 'aniyomi-manga-api.jar')}
        self.assertIn('eu/kanade/tachiyomi/animesource/AnimeSource', video)
        self.assertIn('eu/kanade/tachiyomi/source/CatalogueSource', manga)
        self.assertNotIn('eu/kanade/tachiyomi/source/model/SMangaHomeMetadata', manga)


if __name__ == '__main__': unittest.main()
