import inspect
import unittest
import warnings
from collections import Sequence

from mock import patch
import uuid

from .cuba import CUBA
from .meta_class import api as meta_class


@patch('simphony.core.data_container.CUBA', CUBA)
class TestMetaClass(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        ''' Collect classes that can be instantiated without arguments
        '''
        cls.no_required_args_classes = []

        for name, klass in inspect.getmembers(meta_class, inspect.isclass):
            # Inspect the __init__ signature
            init_spec = inspect.getargspec(klass.__init__)

            # Number of required arguments
            num_required = len(init_spec.args) - len(init_spec.defaults) - 1

            if num_required > 0:
                if not hasattr(cls, 'test_'+name):
                    message = ('Instantiation of `{0}` required {1} arguments '
                               'and is not tested in batch. A test case '
                               '`test_{0}` is not found either. '
                               'Please add a test case.')
                    warnings.warn(message.format(name, num_required))
                continue

            cls.no_required_args_classes.append((name, klass))

    def check_cuds_item(self, instance):
        ''' Check properties of a CUDSItem '''
        self.assertIsInstance(instance.uid, uuid.UUID)
        self.assertIsNotNone(instance.data)

        # uuid is read-only
        with self.assertRaises(AttributeError):
            instance.uid = uuid.uuid4()

    def check_cuds_component(self, instance):
        ''' Check properties of a CUDS Component '''
        self.assertTrue(hasattr(instance, 'description'),
                        'Should have an attribute called `description`')
        self.assertTrue(hasattr(instance, 'name'),
                        'Should have an attribute called `name`')

        # definition is read-only
        with self.assertRaises(AttributeError):
            instance.definition = 'blah'

        # name should be a string
        with self.assertRaises(TypeError):
            instance.name = 1

        # description should be a string
        with self.assertRaises(TypeError):
            instance.description = 1

        # Since NAME and DESCRIPTION are CUBA keys
        # Make sure that their values are stored in
        # the DataContainer as well
        instance.name = 'dummy name'
        self.assertEqual(instance.data[CUBA.NAME], 'dummy name')

        instance.description = 'dummy description'
        self.assertEqual(instance.data[CUBA.DESCRIPTION], 'dummy description')

    def check_model_equation(self, instance):
        ''' Check properties of a ModelEquation '''
        self.assertTrue(hasattr(instance, 'models'),
                        'Should have an attribute called `models`')
        self.assertIsNotNone(instance.models)
        self.assertTrue(hasattr(instance, 'variables'),
                        'Should have an attribute called `variables`')
        self.assertIsNotNone(instance.variables)

        # variables is read-only
        with self.assertRaises(AttributeError):
            instance.variables = ('1', '2')

        # models is read-only
        with self.assertRaises(AttributeError):
            instance.models = []

    def test_all_instantiate(self):
        ''' Test if classes that do not required arguments in init can be instantiated '''  # noqa
        errors = []

        message = ('Error when instantiating {klass} with {error_type}:'
                   '{error_message}')
        # Test instantiation
        for name, klass in self.no_required_args_classes:
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
        for name, klass in self.no_required_args_classes:
            if not issubclass(klass, meta_class.CUDSItem):
                errors.append(message.format(klass=name))

            # Test properties for CUDSItem
            meta_obj = klass()
            self.check_cuds_item(meta_obj)

        if errors:
            self.fail('\n'.join(errors))

    def test_cuds_components_properties(self):
        ''' Test the properties of CUDSComponent '''
        for name, klass in self.no_required_args_classes:
            if issubclass(klass, meta_class.CUDSComponent):
                meta_obj = klass()
                self.check_cuds_component(meta_obj)

    def test_parents(self):
        ''' Test API for parents '''
        for name, klass in self.no_required_args_classes:
            meta_obj = klass()
            self.assertIsInstance(meta_obj.parents, Sequence)

    def test_supported_parameters(self):
        ''' Test API for supported_parameters '''
        for name, klass in self.no_required_args_classes:
            meta_obj = klass()
            self.assertIsInstance(meta_obj.supported_parameters, Sequence)

    def test_Cfd(self):
        ''' Test for Cfd '''
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
        self.check_model_equation(meta_obj)

    def test_ComputationalMethod(self):
        ''' Test for ComputationalMethod '''
        physics_equation = meta_class.PhysicsEquation()
        meta_obj = meta_class.ComputationalMethod(physics_equation)

        # Test setting the attribute on init
        self.assertEqual(meta_obj.physics_equation, physics_equation)

        self.assertEqual(meta_obj.definition,
                         'A computational method according to the RoMM')  # noqa

        self.check_cuds_item(meta_obj)
        self.check_cuds_component(meta_obj)

    def test_LennardJones_6_12(self):
        ''' Test validation code using LennardJones_6_12 '''
        # Material needs to be of shape of 2, both instance of Material
        materials = (meta_class.Material(), meta_class.Material())
        meta_obj = meta_class.LennardJones_6_12(material=materials)

        with self.assertRaises(TypeError):
            # Has to be a float
            meta_obj.van_der_waals_radius = 1

        with self.assertRaises(TypeError):
            # Cannot be None
            meta_obj.van_der_waals_radius = None

        # But this is fine
        meta_obj.van_der_waals_radius = 1.0

        with self.assertRaises(ValueError):
            # Has to be between two materials
            meta_obj.material = [1, 3, 5]

        with self.assertRaises(TypeError):
            # The items of the sequence are not instance of Material
            meta_obj.material = [1, 2]

    def test_Dem(self):
        ''' Test for Dem '''
        # These are all physical equations, therefore valid arguments for DEM
        physics_equations = tuple(
            klass()
            for _, klass in self.no_required_args_classes
            if issubclass(klass, meta_class.PhysicsEquation))

        for physics_equation in physics_equations:
            meta_obj = meta_class.Dem(physics_equation)

        self.check_cuds_item(meta_obj)
        self.check_cuds_component(meta_obj)

    def test_EmptyBoundaryCondition(self):
        ''' Test for EmptyBoundaryCondition '''
        # It can accept any number of materials
        for num_materials in range(5):
            materials = tuple(meta_class.Material()
                              for _ in range(num_materials))
            meta_obj = meta_class.EmptyBoundaryCondition(materials)

        self.check_cuds_item(meta_obj)
        self.check_cuds_component(meta_obj)

    def test_Version(self):
        ''' Test for Version '''
        # This is fine
        meta_obj = meta_class.Version('1', '2', '3', '4')

        # This should raise TypeError because minor/patch/... should be str
        with self.assertRaises(TypeError):
            meta_obj = meta_class.Version(1, '2', '3', '4')

        self.check_cuds_item(meta_obj)

    def test_physics_equation_are_model_equation(self):
        ''' Test all physics equations are model equations '''
        for name, klass in self.no_required_args_classes:
            if issubclass(klass, meta_class.PhysicsEquation):
                self.check_model_equation(klass())

    def test_Coulomb(self):
        meta_class.Coulomb(
            material=(meta_class.Material(), meta_class.Material()))

    def test_CoulombFrictionForce(self):
        # CoulombFrictionForce is a material relation
        # material should be a sequence of Material (any number)
        meta_class.CoulombFrictionForce(
            material=(meta_class.Material(), meta_class.Material()))

    def test_DirichletBoundaryCondition(self):
        meta_class.DirichletBoundaryCondition(
            material=(meta_class.Material(), meta_class.Material()))

    def test_DissipationForce(self):
        meta_class.DissipationForce(
            material=(meta_class.Material(), meta_class.Material()))

    def test_Fem(self):
        meta_class.Fem(physics_equation=meta_class.PhysicsEquation())

    def test_Fvm(self):
        meta_class.Fvm(physics_equation=meta_class.PhysicsEquation())

    def test_InteratomicPotential(self):
        meta_class.InteratomicPotential(
            material=(meta_class.Material(), meta_class.Material()))

    def test_MaterialRelation(self):
        meta_class.MaterialRelation(
            material=(meta_class.Material(), meta_class.Material()))

    def test_NeumannBoundaryCondition(self):
        meta_class.NeumannBoundaryCondition(
            material=(meta_class.Material(), meta_class.Material(),
                      meta_class.Material()))

    def test_PairPotential(self):
        meta_class.PairPotential(
            material=(meta_class.Material(), meta_class.Material()))

    def test_SjkrCohesionForce(self):
        meta_class.SjkrCohesionForce(
            material=(meta_class.Material(), meta_class.Material()))

    def test_Sph(self):
        meta_class.Sph(physics_equation=meta_class.PhysicsEquation())

    def test_SurfaceTensionRelation(self):
        meta_class.SurfaceTensionRelation(
            material=(meta_class.Material(), meta_class.Material()))

    def test_Verlet(self):
        meta_class.Verlet(physics_equation=meta_class.PhysicsEquation())
