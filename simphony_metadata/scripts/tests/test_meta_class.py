import inspect
import unittest
import warnings

import uuid

from simphony.core.data_container import DataContainer
from simphony_metadata.scripts.tests.meta_class import api as meta_class


class TestMetaClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ''' Collect classes that can be instantiated without arguments
        '''
        cls.instantiable_classes = []

        for name, klass in inspect.getmembers(meta_class, inspect.isclass):
            init_spec = inspect.getargspec(klass.__init__)
            required_args = len(init_spec.args) - len(init_spec.defaults) - 1

            if required_args > 0:
                if not hasattr(cls, 'test_'+name):
                    message = ('Instantiation of `{0}` required {1} arguments '
                               'and is not tested in batch. A test case '
                               '`test_{0}` is not found either. '
                               'Please add a test case.')
                    warnings.warn(message.format(name, required_args))
                continue

            cls.instantiable_classes.append((name, klass))

    def check_cuds_item(self, instance):
        ''' Check attributes of a CUDSItem '''
        self.assertIsInstance(instance.uuid, uuid.UUID)
        self.assertIsInstance(instance.data, DataContainer)

    def check_cuds_component(self, instance):
        ''' Check attributes of a CUDS Component '''
        self.assertTrue(hasattr(instance, 'description'),
                        'Should have an attribute called `description`')
        self.assertTrue(hasattr(instance, 'name'),
                        'Should have an attribute called `name`')

    def check_model_equation(self, instance):
        ''' Check attributes of a ModelEquation '''
        self.assertTrue(hasattr(instance, 'models'),
                        'Should have an attribute called `models`')
        self.assertTrue(hasattr(instance, 'variables'),
                        'Should have an attribute called `variables`')

    def test_all_instantiate(self):
        ''' Test if classes that do not required arguments in init can be instantiated '''  # noqa
        errors = []

        message = ('Error when instantiating {klass} with {error_type}:'
                   '{error_message}')
        # Test instantiation
        for name, klass in self.instantiable_classes:
            try:
                klass()
            except Exception as exception:
                errors.append(
                    message.format(klass=name,
                                   error_type=type(exception).__name__,
                                   error_message=str(exception)))
        if errors:
            self.fail('\n'.join(errors))

    def test_all_inherit_cuds_item(self):
        ''' Test if all classes that can be instantiated inherit from CUDSItem '''  # noqa
        errors = []

        message = '{klass} does not inherit from CUDSItem'

        # Test subclass
        for name, klass in self.instantiable_classes:
            if not issubclass(klass, meta_class.CUDSItem):
                errors.append(message.format(klass=name))

            # Test properties for CUDSItem
            meta_obj = klass()
            self.check_cuds_item(meta_obj)

        if errors:
            self.fail('\n'.join(errors))

    def test_cuds_components(self):
        for name, klass in self.instantiable_classes:
            if issubclass(klass, meta_class.CUDSComponent):
                meta_obj = klass()
                self.check_cuds_component(meta_obj)

    def test_model_equation(self):
        for name, klass in self.instantiable_classes:
            if issubclass(klass, meta_class.ModelEquation):
                meta_obj = klass()
                self.check_model_equation(meta_obj)

    def test_Cfd(self):
        gravity_model = meta_class.GravityModel()

        meta_obj = meta_class.Cfd(gravity_model)

        # Test setting the attribute on init
        self.assertEqual(meta_obj.gravity_model, gravity_model)

        self.assertEqual(meta_obj.definition,
                         'Computational fluid dynamics general (set of ) equations for momentum, mass and energy')  # noqa

        # Test the default values
        self.assertIsInstance(meta_obj.compressibility_model,
                              meta_class.IncompressibleFluidModel)
        self.assertIsInstance(meta_obj.thermal_model,
                              meta_class.IsothermalModel)
        self.assertIsInstance(meta_obj.turbulence_model,
                              meta_class.LaminarFlowModel)
        self.assertIsInstance(meta_obj.multiphase_model,
                              meta_class.SinglePhaseModel)
        self.assertIsInstance(meta_obj.rheology_model,
                              meta_class.NewtonianFluidModel)
        self.assertIsInstance(meta_obj.electrostatic_model,
                              meta_class.ConstantElectrostaticFieldModel)

        self.check_cuds_item(meta_obj)
        self.check_cuds_component(meta_obj)

    def test_ComputationalMethod(self):
        physics_equation = meta_class.PhysicsEquation()
        meta_obj = meta_class.ComputationalMethod(physics_equation)

        # Test setting the attribute on init
        self.assertEqual(meta_obj.physics_equation, physics_equation)

        self.assertEqual(meta_obj.definition,
                         'A computational method according to the RoMM')  # noqa

        self.check_cuds_item(meta_obj)
        self.check_cuds_component(meta_obj)

    def test_validation_with_LennardJones(self):
        meta_obj = meta_class.LennardJones_6_12()

        with self.assertRaises(TypeError):
            # Has to be a float
            meta_obj.van_der_waals_radius = 1

        # But this is fine
        meta_obj.van_der_waals_radius = 1.0

        with self.assertRaises(ValueError):
            # Has to be between two materials
            meta_obj.material = [1, 3, 5]

        with self.assertRaises(TypeError):
            # The items of the sequence are not instance of Material
            meta_obj.material = [1, 2]

        # This is fine
        meta_obj.material = [meta_class.Material(), meta_class.Material()]
