import KratosMultiphysics

import KratosMultiphysics.StructuralMechanicsApplication as StructuralMechanicsApplication
import KratosMultiphysics.KratosUnittest as KratosUnittest


class TestPatchTestShellsStressRec(KratosUnittest.TestCase):
    def setUp(self):
        pass

    def _add_variables(self,mp):
        mp.AddNodalSolutionStepVariable(KratosMultiphysics.DISPLACEMENT)
        mp.AddNodalSolutionStepVariable(KratosMultiphysics.ROTATION)
        mp.AddNodalSolutionStepVariable(KratosMultiphysics.REACTION)
        mp.AddNodalSolutionStepVariable(KratosMultiphysics.REACTION_MOMENT)
        mp.AddNodalSolutionStepVariable(KratosMultiphysics.VOLUME_ACCELERATION)
        mp.AddNodalSolutionStepVariable(StructuralMechanicsApplication.POINT_LOAD)


    def _add_dofs(self,mp):
        # Adding the dofs AND their corresponding reaction!
        KratosMultiphysics.VariableUtils().AddDof(KratosMultiphysics.DISPLACEMENT_X, KratosMultiphysics.REACTION_X,mp)
        KratosMultiphysics.VariableUtils().AddDof(KratosMultiphysics.DISPLACEMENT_Y, KratosMultiphysics.REACTION_Y,mp)
        KratosMultiphysics.VariableUtils().AddDof(KratosMultiphysics.DISPLACEMENT_Z, KratosMultiphysics.REACTION_Z,mp)

        KratosMultiphysics.VariableUtils().AddDof(KratosMultiphysics.ROTATION_X, KratosMultiphysics.REACTION_MOMENT_X,mp)
        KratosMultiphysics.VariableUtils().AddDof(KratosMultiphysics.ROTATION_Y, KratosMultiphysics.REACTION_MOMENT_Y,mp)
        KratosMultiphysics.VariableUtils().AddDof(KratosMultiphysics.ROTATION_Z, KratosMultiphysics.REACTION_MOMENT_Z,mp)


    def _create_nodes(self,mp,element_name):
        mp.CreateNewNode(1, -0.5, - 0.45,  0.1)
        mp.CreateNewNode(2,  0.7,  -0.5,   0.2)
        mp.CreateNewNode(3,  0.55,  0.6,   0.15)
        mp.CreateNewNode(4, -0.48,  0.65,  0.0)
        mp.CreateNewNode(5,  0.02, -0.01, -0.15)

        if element_name.endswith("4N"): # create aditional nodes needed for quad-setup
            mp.CreateNewNode(6, -0.03, -0.5,   0.0)
            mp.CreateNewNode(7,  0.51,  0.02,  0.03)
            mp.CreateNewNode(8, -0.01,  0.52, -0.05)
            mp.CreateNewNode(9, -0.49, -0.0,   0.0)


    def _create_elements(self,mp,element_name):
        if element_name.endswith("4N"): # Quadrilaterals
            mp.CreateNewElement(element_name, 1, [1,6,5,9], mp.GetProperties()[1])
            mp.CreateNewElement(element_name, 2, [6,2,7,5], mp.GetProperties()[1])
            mp.CreateNewElement(element_name, 3, [5,7,3,8], mp.GetProperties()[1])
            mp.CreateNewElement(element_name, 4, [9,5,8,4], mp.GetProperties()[1])
        else: # Triangles
            mp.CreateNewElement(element_name, 1, [1,2,5], mp.GetProperties()[1])
            mp.CreateNewElement(element_name, 2, [2,3,5], mp.GetProperties()[1])
            mp.CreateNewElement(element_name, 3, [3,4,5], mp.GetProperties()[1])
            mp.CreateNewElement(element_name, 4, [4,1,5], mp.GetProperties()[1])


    def _apply_dirichlet_BCs(self,mp):
        KratosMultiphysics.VariableUtils().ApplyFixity(KratosMultiphysics.DISPLACEMENT_X, True, mp.Nodes)
        KratosMultiphysics.VariableUtils().ApplyFixity(KratosMultiphysics.DISPLACEMENT_Y, True, mp.Nodes)
        KratosMultiphysics.VariableUtils().ApplyFixity(KratosMultiphysics.DISPLACEMENT_Z, True, mp.Nodes)
        KratosMultiphysics.VariableUtils().ApplyFixity(KratosMultiphysics.ROTATION_X, True, mp.Nodes)
        KratosMultiphysics.VariableUtils().ApplyFixity(KratosMultiphysics.ROTATION_Y, True, mp.Nodes)
        KratosMultiphysics.VariableUtils().ApplyFixity(KratosMultiphysics.ROTATION_Z, True, mp.Nodes)


    def _apply_neumann_BCs(self,mp):
        for node in mp.Nodes:
            node.SetSolutionStepValue(StructuralMechanicsApplication.POINT_LOAD,0,[6.1,-5.5,8.9])
            mp.CreateNewCondition("PointLoadCondition3D1N",1,[node.Id],mp.GetProperties()[1])


    def _apply_material_properties(self,mp):
        #define properties
        mp.GetProperties()[1].SetValue(KratosMultiphysics.YOUNG_MODULUS,100e3)
        mp.GetProperties()[1].SetValue(KratosMultiphysics.POISSON_RATIO,0.3)
        mp.GetProperties()[1].SetValue(KratosMultiphysics.THICKNESS,1.0)
        mp.GetProperties()[1].SetValue(KratosMultiphysics.DENSITY,1.0)

        g = [0,0,0]
        mp.GetProperties()[1].SetValue(KratosMultiphysics.VOLUME_ACCELERATION,g)

        cl = StructuralMechanicsApplication.LinearElasticPlaneStress2DLaw()

        mp.GetProperties()[1].SetValue(KratosMultiphysics.CONSTITUTIVE_LAW,cl)


    def _solve(self,mp):
        #define a minimal newton raphson solver
        linear_solver = KratosMultiphysics.SkylineLUFactorizationSolver()
        builder_and_solver = KratosMultiphysics.ResidualBasedBlockBuilderAndSolver(linear_solver)
        scheme = KratosMultiphysics.ResidualBasedIncrementalUpdateStaticScheme()
        convergence_criterion = KratosMultiphysics.ResidualCriteria(1e-14,1e-20)
        convergence_criterion.SetEchoLevel(0)

        max_iters = 20
        compute_reactions = True
        reform_step_dofs = True
        calculate_norm_dx = False
        move_mesh_flag = True
        strategy = KratosMultiphysics.ResidualBasedNewtonRaphsonStrategy(mp,
                                                                        scheme,
                                                                        convergence_criterion,
                                                                        builder_and_solver,
                                                                        max_iters,
                                                                        compute_reactions,
                                                                        reform_step_dofs,
                                                                        move_mesh_flag)
        strategy.SetEchoLevel(0)
        strategy.Initialize()
        strategy.Check()
        strategy.Solve()


    def _check_results(self,node,displacement_results, rotation_results):
        ##check that the results are exact on the node
        disp = node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT)
        self.assertAlmostEqual(disp[0], displacement_results[0], 10)
        self.assertAlmostEqual(disp[1], displacement_results[1], 10)
        self.assertAlmostEqual(disp[2], displacement_results[2], 10)

        rot = node.GetSolutionStepValue(KratosMultiphysics.ROTATION)
        self.assertAlmostEqual(rot[0], rotation_results[0], 10)
        self.assertAlmostEqual(rot[1], rotation_results[1], 10)
        self.assertAlmostEqual(rot[2], rotation_results[2], 10)


    def _check_results_stress(self,element,stress_variable,reference_stress_results,processInfo):
        ##check that the results are exact on the first gauss point
        ##only upper triangle of stresses are checked due to symmetry
        stress = element.CalculateOnIntegrationPoints(stress_variable, processInfo)[0]
        self.assertAlmostEqual(stress[0,0], reference_stress_results[0])
        self.assertAlmostEqual(stress[0,1], reference_stress_results[1])
        self.assertAlmostEqual(stress[0,2], reference_stress_results[2])
        self.assertAlmostEqual(stress[1,1], reference_stress_results[3])
        self.assertAlmostEqual(stress[1,2], reference_stress_results[4])
        self.assertAlmostEqual(stress[2,2], reference_stress_results[5])


    def execute_shell_test(self, current_model, element_name, displacement_results, rotation_results, shell_stress_middle_surface_results, shell_stress_top_surface_results, shell_stress_bottom_surface_results, shell_von_mises_result,do_post_processing):
        mp = current_model.CreateModelPart("solid_part")
        mp.SetBufferSize(2)

        self._add_variables(mp)
        self._apply_material_properties(mp)
        self._create_nodes(mp,element_name)
        self._add_dofs(mp)
        self._create_elements(mp,element_name)

        #create a submodelpart for dirichlet boundary conditions
        bcs_dirichlet = mp.CreateSubModelPart("BoundaryCondtionsDirichlet")
        bcs_dirichlet.AddNodes([1,2,4])

        #create a submodelpart for neumann boundary conditions
        bcs_neumann = mp.CreateSubModelPart("BoundaryCondtionsNeumann")
        bcs_neumann.AddNodes([3])

        self._apply_dirichlet_BCs(bcs_dirichlet)
        self._apply_neumann_BCs(bcs_neumann)
        self._solve(mp)

        # Check displacements
        self._check_results(mp.Nodes[3],displacement_results, rotation_results)

        # Check stresses at each surface
        self._check_results_stress(mp.Elements[1],
                                   StructuralMechanicsApplication.SHELL_STRESS_MIDDLE_SURFACE,
                                   shell_stress_middle_surface_results,mp.ProcessInfo)
        self._check_results_stress(mp.Elements[1],
                                   StructuralMechanicsApplication.SHELL_STRESS_TOP_SURFACE,
                                   shell_stress_top_surface_results,mp.ProcessInfo)
        self._check_results_stress(mp.Elements[1],
                                   StructuralMechanicsApplication.SHELL_STRESS_BOTTOM_SURFACE,
                                   shell_stress_bottom_surface_results,mp.ProcessInfo)

        # Check results of doubles on 2nd element @ Gauss Point [0] only
        self.assertAlmostEqual(mp.Elements[1].CalculateOnIntegrationPoints(StructuralMechanicsApplication.VON_MISES_STRESS,
                               mp.ProcessInfo)[0], shell_von_mises_result, 9)

        if do_post_processing:
            self.__post_process(mp)


    def test_thin_shell_triangle(self):
        element_name = "ShellThinElementCorotational3D3N"
        displacement_results = [0.000232466935 , -0.00022337867 , 0.000256728258]
        rotation_results     = [0.000362805651 , -0.000192603777 , -0.000468264833]
        shell_stress_middle_surface_results = [1.330532185831 , 0.264532374393 , 0.0 , 5.017119730101 , 0.0 , 0.0]
        shell_stress_top_surface_results    = [-1.227921495072 , 0.431252225426 , 0.0 , -1.60308025618 , 0.0 , 0.0]
        shell_stress_bottom_surface_results = [3.888985866804 , 0.097812523361 , 0.0 , 11.637319716442 , 0.0 , 0.0]
        shell_von_mises_result = 6.84404599900034

        current_model = KratosMultiphysics.Model()
        self.execute_shell_test(current_model,
                                element_name,
                                displacement_results,
                                rotation_results,
                                shell_stress_middle_surface_results,
                                shell_stress_top_surface_results,
                                shell_stress_bottom_surface_results,
                                shell_von_mises_result,
                                False) # Do PostProcessing for GiD?


    def test_thick_shell_triangle(self):
        element_name = "ShellThickElementCorotational3D3N"
        displacement_results = [7.18429456e-05 , -0.0001573361523 , 0.0005263535842]
        rotation_results     = [0.0003316611414 , -0.0002797797097 , 4.922597e-07]
        shell_stress_middle_surface_results = [0.32465769837 , 2.916044245593 , 0.281946444464 , -3.126126456163 , -1.805596378534 , 0.0]
        shell_stress_top_surface_results    = [-4.155385244644 , -3.434557725121 , 0.0 , -9.907162942127 , 0.0 , 0.0]
        shell_stress_bottom_surface_results = [4.804700641385 , 9.266646216307 , 0.0 , 3.6549100298 , 0.0 , 0.0]
        shell_von_mises_result = 16.628137698179042

        current_model = KratosMultiphysics.Model()
        self.execute_shell_test(current_model,
                                element_name,
                                displacement_results,
                                rotation_results,
                                shell_stress_middle_surface_results,
                                shell_stress_top_surface_results,
                                shell_stress_bottom_surface_results,
                                shell_von_mises_result,
                                False) # Do PostProcessing for GiD?


    def test_thin_shell_quadrilateral(self):
        element_name = "ShellThinElementCorotational3D4N"
        displacement_results = [0.0021867287711 , -0.002169253367 , 0.0007176841015]
        rotation_results     = [0.002816872164 , 0.0008161241026 , -0.0069076664086]
        shell_stress_middle_surface_results = [3.272955597478 , -11.215566923738 , 0.0 , 3.360152391538 , 0.0 , 0.0]
        shell_stress_top_surface_results    = [20.197335966016 , 4.515326224888 , 0.0 , -8.626180886984 , 0.0 , 0.0]
        shell_stress_bottom_surface_results = [-13.651424771092 , -26.94646007236 , 0.0 , 15.346485670044 , 0.0 , 0.0]
        shell_von_mises_result = 53.00672171174518

        current_model = KratosMultiphysics.Model()
        self.execute_shell_test(current_model,
                                element_name,
                                displacement_results,
                                rotation_results,
                                shell_stress_middle_surface_results,
                                shell_stress_top_surface_results,
                                shell_stress_bottom_surface_results,
                                shell_von_mises_result,
                                False) # Do PostProcessing for GiD?


    def test_thick_shell_quadrilateral(self):
        element_name = "ShellThickElementCorotational3D4N"
        displacement_results = [0.000356813514 , -0.00063451962 , 0.001277536105]
        rotation_results     = [0.001208329991 , -0.000409163542 , -0.001166832572]
        shell_stress_middle_surface_results = [2.673886114206 , -3.482959961533 , 0.751398508523 , 2.763048319957 , 6.546366049819 , 0.0]
        shell_stress_top_surface_results    = [9.0127433219 , 0.557224675217 , 0.0 , -50.720551115113 , 0.0 , 0.0]
        shell_stress_bottom_surface_results = [-3.664971093553 , -7.523144598382 , 0.0 , 56.246647754966 , 0.0 , 0.0]
        shell_von_mises_result = 59.607489872219794

        current_model = KratosMultiphysics.Model()
        self.execute_shell_test(current_model,
                                element_name,
                                displacement_results,
                                rotation_results,
                                shell_stress_middle_surface_results,
                                shell_stress_top_surface_results,
                                shell_stress_bottom_surface_results,
                                shell_von_mises_result,
                                False) # Do PostProcessing for GiD?


    def __post_process(self, main_model_part):
        from gid_output_process import GiDOutputProcess
        self.gid_output = GiDOutputProcess(main_model_part,
                                    "gid_output",
                                    KratosMultiphysics.Parameters("""
                                        {
                                            "result_file_configuration" : {
                                                "gidpost_flags": {
                                                    "GiDPostMode": "GiD_PostBinary",
                                                    "WriteDeformedMeshFlag": "WriteUndeformed",
                                                    "WriteConditionsFlag": "WriteConditions",
                                                    "MultiFileFlag": "SingleFile"
                                                },
                                                "nodal_results"       : ["DISPLACEMENT", "ROTATION", "POINT_LOAD"],
                                                "gauss_point_results" : ["GREEN_LAGRANGE_STRAIN_TENSOR","CAUCHY_STRESS_TENSOR"]
                                            }
                                        }
                                        """)
                                    )

        self.gid_output.ExecuteInitialize()
        self.gid_output.ExecuteBeforeSolutionLoop()
        self.gid_output.ExecuteInitializeSolutionStep()
        self.gid_output.PrintOutput()
        self.gid_output.ExecuteFinalizeSolutionStep()
        self.gid_output.ExecuteFinalize()

if __name__ == '__main__':
    KratosUnittest.main()
