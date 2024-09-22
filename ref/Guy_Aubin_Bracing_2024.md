OPEN
Automated design of **nighttime** braces for **adolescent** idiopathic scoliosis with global shape optimization using 

# A Patient‑Specifc Fnite Element

## Model

AymericGuy 1,2, Maxence Coulombe2,3, Hubert Labelle2,3, Soraya Barchi2 & 
Carl‑ÉricAubin1,2,3* Adolescent idiopathic scoliosis is a complex three-dimensional deformity of the spine, the moderate forms of which require treatment with an orthopedic brace. Existing brace design approaches rely mainly on empirical manual processes, vary considerably depending on the training and expertise of the orthotist, and do not always guarantee biomechanical efectiveness. To address these issues, we propose a new automated design method for creating bespoke nighttime braces requiring virtually no user input in the process. From standard biplanar radiographs and a surface topography torso scan, a personalized fnite element model of the patient is created to simulate bracing and the resulting spine growth over the treatment period. Then, the topography of an automatically generated brace is modifed and simulated over hundreds of iterations by a clinically driven optimization algorithm aiming to improve brace immediate and long-term efectiveness while respecting safety thresholds. This method was clinically tested on 17 patients prospectively recruited. The optimized braces showed a highly efective immediate correction of the thoracic and lumbar curves (70% and 90% respectively), with no modifcations needed to ft the braces onto the patients. In addition, the simulated lumbar lordosis and thoracic apical rotation were improved by 5°± 3° and 2° ± 3° respectively. Our approach distinguishes from traditional brace design as it relies solely on biomechanically validated models of the patient's digital twin and a design strategy that is entirely abstracted from empirical knowledge. It provides clinicians with an efcient way to create efective braces without relying on lengthy manual processes and variable orthotist expertise to ensure a proper correction of scoliosis. Adolescent idiopathic scoliosis (AIS) is a complex three-dimensional (3D) deformation of the spine that afects 2 to 4% of the pediatric population and onsets afer 10 years of age1. AIS tends to progress during the peripubertal growth spurt, as the magnitude of the scoliotic curves increases and the deformity worsens. Tis pathomechanism of progression can be biomechanically explained by the Hueter–Volkmann principle describing how bone growth is favored in relative tension on the convex side of the deformity and inhibited in relative compression on its concave side, leading to vertebral wedging over time2. Tis is commonly referred to as the scoliosis vicious cycle3. AIS patients progressing over 45° of Cobb angle generally require an instrumentation and spinal fusion surgery, an invasive procedure with undesirable side-efects such as a loss of mobility and potential complications over time4.

Bracing is the most common conservative treatment aiming at controlling this progression to avoid a surgical intervention. Braces are generally prescribed for full-time wear between 18 and 23 h/day for an average treatment duration of 2 years, or until skeletal maturity. Most take the form of thoracolumbosacral orthoses: rigid 1Polytechnique Montreal, 2500 Chemin de Polytechnique, Montreal, QC H3T 1J4, Canada. 2Sainte-Justine University Hospital Center, Montreal, QC, Canada. 3Université de Montréal, Montreal, QC, Canada. *email: 
carl-eric.aubin@polymtl.ca plastic shells that apply corrective forces onto the patient's torso at predetermined contact points using tensioned closure straps5. It is hypothesized that this correction may contribute to break away from the scoliosis vicious cycle by aligning the spine in-brace and symmetrizing the compressive forces acting on the vertebral epiphyseal growth plates3. Bracing has been documented as an efective treatment when compared to observation alone6.

However, brace-wear compliance is far from optimal, even if it is strongly linked to treatment success. Most centers report compliance rates on the order of 60%7,8, with an average daily brace wear of around 13 h across patients6,9. To mitigate this poor adherence to treatment, nighttime braces can be prescribed and are generally better accepted by patients because they have a lesser impact on daily activities. Nighttime braces are only worn during sleep and incorporate more aggressive correction features to compensate for the decreased wear time. As a result, pronounced trunk rotation and shoulder imbalance can lead to comfort issues10, while efective correction of thoracic curves is limited due to the intrinsic stifness of the ribcage11. Studies have shown comparable efectiveness between full-time and nighttime braces12,13, but more high-quality trials are required to confrm their equivalence14. Nevertheless, nighttime braces are a useful compromise to ease patients into the brace treatment.

Nowadays, braces are designed using a computer-assisted design/manufacturing approach (CAD/CAM)15, where a torso surface topography scan is imported in a CAD sofware in which an orthotist models contact and relief regions to create a deformed positive mold of the patient's trunk5. Tis mold is carved by a numerical router in a block of foam around which a plastic sheet is thermoformed. Te plastic shell is then trimmed, straps are added, and the brace is fnally ftted on the patient in the clinic to ensure comfort. While manufacturing is generally similar across centers, various brace design approaches and corrective strategies exist16. Signifcant variability is observed between these sometimes-conficting biomechanical concepts, and brace quality depends on many factors including the orthotist's expertise, the chosen design protocol, and the overall treatment strategy17. 

Current braces are therefore mainly designed using empirical knowledge acquired over many years of experience, difcult to transfer outside of a single clinical center. In addition, published clinical trials contain several biases and heterogeneous patient cohorts that render a structured comparison of each approach impossible18. To this day, the best brace design method is still unknown16, and standardization remains insufcient to ensure a repeatable, quality treatment across centers with variable expertise17,19.

Many studies have correlated diferent alignment metrics to treatment success, but few provide in-depth biomechanical assessments of the efects of brace wear. Greater in-brace correction in the coronal plane—Cobb angles of the main thoracic (MT) and thoracolumbar/lumbar (TL/L) curves, greater axial vertebral rotation 
(AVR) correction in the transverse plane around the apex of the curve, and a focus towards preserving or increasing the healthy sagittal curves—thoracic kyphosis (TK) and lumbar lordosis (LL), were shown to be predictive of treatment success20–22. As a result, orthotists need to balance correction in the three anatomical planes to ensure an efective clinical impact. Tey usually aim at achieving a minimum of 50% correction of the main curve's Cobb angle14, while simultaneously trying to move the spine into a normal sagittal alignment, generally to avoid brace-induced fatback, and reduce some of the deformity's rotational component19.

A few research groups have created numerical tools to study and better understand brace biomechanics in 3D23,24. Specifcally, our group has extensively developed a patient-specifc fnite element model (FEM) constructed from the patient's torso surface topography scan, the brace's 3D model, and a 3D reconstruction of the patient's spine, ribcage, pelvis and sternum based on biplanar standing radiographs25–27. Tis FEM, previously validated using clinical data26, can simulate brace donning and tightening and was employed to study the impact of brace design features in a structured approach with minimal biases17,28. It was subsequently adapted to simulate nighttime bracing29,30. In parallel, an analogous FEM was also developed to simulate vertebral growth modulation of progressive deformities in AIS31, which was further adapted for fusionless surgical applications32,33, and validated for bracing specifcally[34].

Our bracing FEM has been implemented in a clinical setting to assist orthotists in brace design9,35, 36. In a randomized controlled trial, 120 patients were separated into two groups: one with standard CAD/CAM braces, and one with CAD/CAM braces that had been further improved using the patient-specifc FEM. In the latter, orthotists would design a brace, simulate it on the digital patient, modify their design based on the simulated correction, cutaneous pressures, and skin-to-brace distances, and repeat the process until a satisfactory design was achieved. Te braces created were lighter, thinner, and covered less surface on the torso, but were not found to be diferent from standard CAD/CAM braces, in terms of correction of the scoliotic deformity, brace-wear compliance, or quality of life9. Adding manual improvements steps using the FEM lengthened the quantity of work per brace required from the orthotist, roughly 30 min per design iteration, which limited the process to an average of three iterations in practice35. Also, the design modifcations were chosen and implemented by the orthotist, such that the fnal braces still converged towards their usual empirical corrective strategies with minor improvements. Tis trial confrmed the clinical utility of using a patient-specifc FEM for brace design, but the full capacity to optimize correction while providing an efective useable tool transposable to many centers remains to be established. To address these challenges, the objective of this work was to develop a new automated design method producing nighttime braces independently from empirical knowledge, and validate its clinical efcacy on a patient cohort. Our hypothesis was that a global shape optimization process leveraging a patient-specifc FEM could autonomously create braces with sufcient in-brace correction (over 50%) without the need for any manual design input.

## Methods Cases And Initial Data For Clinical Validation

Seventeen skeletally immature AIS patients between 10 and 16 years of age and prescribed with a nighttime brace for an expected treatment duration of 2 years were prospectively recruited between December 2021 and August 2022. Inclusion followed the Scoliosis Research Society standardized criteria: no prior treatment, skeletal maturity Risser score between 0 and 2, main curve Cobb angle measured at the presenting visit between 20° and 45°37. Te study protocol was approved by our Institutional Review Board (Sainte-Justine University Hospital Center, Montreal, Canada), all experiments were performed in accordance with the Declaration of Helsinki, and all patients and their parents and/or legal guardians provided written informed consent.

At each patient's initial visit, a standing 3D surface topography of the torso was acquired using an infrared structured light sensor (Structure Sensor, Occipital Inc. Boulder, CO, USA), as well as standing biplanar radiographs using a calibrated low-dose digital radiography system (EOS System, EOS Imaging, Paris, France). From these radiographs, a 3D reconstruction of the spine, ribcage, pelvis and sternum was constructed using a previously described parametric registration method based on transversal and longitudinal inferences38.

For each patient, a brace was designed using a global shape optimization method leveraging a patient-specifc FEM. Except for two manual alignment steps requiring rapid user input (<5 min), the totality of design steps were automatically executed by an algorithm managing every step of the process in the Matlab environment (Matlab R2021a, MathWorks, Natick, MA, USA), and its execution time was measured. Depending on the fow of patient recruitment, this execution was parallelized on a single personal computer, up to four simultaneous patients.

## Creation Of The Patient‑Specifc Fem

For each patient, the torso's 3D surface scan was superimposed on the skeleton's 3D reconstruction in two steps, frst by automatically aligning the axes of the principal components of variance calculated for each point cloud, then by manually fne-tuning the alignment to ensure concordance with the clinical images. Tey were then used to generate a previously described and validated patient-specifc FEM26,34, 39, briefy summarized here.

Te resulting registered patient geometry was imported in a fnite element analysis sofware (ANSYS Mechanical 2020 R1, Ansys Inc., Canonsburg, PA, USA). A global coordinate system was defned such that the x-axis pointed anteriorly, the y-axis pointed lef laterally, and the z-axis pointed cranially. Osseous structures were modeled as hexahedral structural solid elements (thoracic and lumbar vertebral bodies, intervertebral disks) and elastic beam elements (vertebral processes, ribs, sternum, and pelvis). Ligaments, internal sof tissues and joints were modeled as tension springs and beam elements. Te torso skin geometry was represented by shell elements with constant thickness. Material properties of all anatomical structures were taken from experimental cadaveric studies40,41. An estimate of spinal fexibility based on the manipulation of the patient's torso by the treating orthopedist at clinical evaluation was factored into the intervertebral disk stifness. Te FEM creation is illustrated on Fig. 1.

## Automatic Generation Of Braces

![2_Image_0.Png](2_Image_0.Png)

![2_Image_1.Png](2_Image_1.Png)

Initial brace defnition Using the patient-specifc FEM, vertebra T1 was frst aligned with the centroid of L5's endplate to correct coronal and sagittal imbalances, its x and y displacements were fxed to only permit craniocaudal movement, and all degrees of freedom of the pelvis were blocked. Displacements (ui, where i = x, y and z directions) were then imposed onto the nodes corresponding to the lef (L) and right (R) pedicles of vertebrae T2 to L4 with the goal 

3
Figure 1. Creation of the patient-specifc FEM from standard biplanar radiographs and a surface topography 

![2_image_2.png](2_image_2.png)

scan of the torso. Elements representing the internal sof tissues and connecting the torso skin to the skeleton are not shown for clarity. of mirroring their coordinates with respect to the sagittal plane to achieve maximal over-correction (Eq. 1). A 
weight W factored the amount of applied displacement to the desired value: W = 0 corresponded to the initial undeformed geometry, W = 0.5 to a spine perfectly aligned onto the sagittal plane, and W = 1 to a fully overcorrected spine with an inverted deformity.

4

![3_image_2.png](3_image_2.png)

Applied displacements = W (1) ∗
$$\left(\begin{array}{c}{{u_{x_{L}}=(x_{R}-x_{L})}}\\ {{u_{x_{R}}=(x_{L}-x_{L})}}\end{array}\right.$$
Applied displacements $=W*\frac{1}{2}$. 
$$(1)$$
T2−L4**pedicles**
$$\left|\begin{array}{c}{{u_{x_{R}}=(x_{L}-x_{R})}}\\ {{u_{y_{L}}=-\left(y_{R}+y_{L}\right)}}\\ {{u_{y_{R}}=-\left(y_{L}+y_{R}\right)}}\\ {{u_{z_{L}}=(z_{R}-z_{L})}}\\ {{u_{z_{R}}=(z_{L}-z_{R})}}\end{array}\right.$$
In a stepwise manner, weight W was increased from 0 to 1 by increments of 0.1. At every step, the fnite element model was solved, and displacements of the vertebral pedicles caused the connected internal structures and the skin to deform. W's increase was stopped if any element distortion in the deformed geometry exceeded the default program-controlled thresholds for convergence. Te deformed skin corresponding to the maximal achieved overcorrection was extracted and converted to a stereolithography (STL) format. Finally, superior and inferior limits were added by manually aligning a spline onto the STL to create the cuts: superior limits were drawn to cover the trunk up to the axilla on the convex side of the thoracic deformity, and inferior limits to cover the trochanter on the ipsilateral side while leaving the contralateral iliac crest free. Te resulting geometry was used as the internal surface of the initial brace shape in the optimization process (Fig. 2). Optimization‑modifed brace shapes

![3_image_0.png](3_image_0.png) Te optimization process modifed the brace topography to generate new shapes at every iteration (Fig. 3). To do so, the initial brace geometry was frst imported as a point cloud. Coordinates were converted from the cartesian to the cylindrical coordinate system and the brace points were separated into patches (subsections) according to a cylindrical 6×6 grid in the z and φ directions. Te radial (ρ) coordinates of the points in each patch were ofset by modifable values: a negative ρ ofset translated the ρ coordinates of all patch points closer to the origin (pressure area) and a positive ρ ofset translated these points further from the origin (relief area). Tis ρ ofset Figure 2. Generation of the initial brace shape: top row represents a top view closeup of a single vertebra 

![3_image_1.png](3_image_1.png)

and illustrates the applied overcorrection, achieved by imposing displacements according to Eq. 1 onto the vertebral pedicle nodes (L for lef, R for right). Over-correction weight W is increased iteratively from 0 to 1, or until element distortion exceeds the FEM threshold. Bottom row represents a posterior view of the FE patient onto which a maximal over-correction (Wmax) is applied. Te skin deforms in response to the applied displacements and the resulting geometry is cut by ftted splines to create the inner surface of the initial brace shape. Translucency was added to the skin elements (bottom lef & center-lef) to view the internal structures. Beam and spring elements representing internal sof tissues and connecting the torso skin to the skeleton were not shown for clarity.

![4_image_0.png](4_image_0.png)

5
Figure 3. Modifcation of the brace shape by the optimization process (anterior view). A 6×6 grid (orange 

![4_image_1.png](4_image_1.png)

dotted lines) in cylindrical coordinates separated the brace surface into patches and optimization variable ρ ofset translated their coordinates in the radial direction. Te resulting brace was then smoothed, a frontal opening was created, and straps were added automatically. vector, of length equal to the total number of patches (36), was the variable vector controlled by the optimization process. To constrain the optimization inside safe limits, the range of possible ρ ofsets was set at [− 25,+25] mm.

Once the ρ ofset vector was applied to the brace points, the geometry was smoothed to fuse the ofset slices together and remove aggressive topographical asperities, a frontal opening was created by removing the points falling into an arc of 20° in the φ direction centered around the frontal axis, and two or three straps were placed by automatically selecting points on each side of the opening falling closest to a proportional normalized height vector of [0.33, 0.66] or [0.25, 0.5, 0.75].

## Evaluation Of Brace Biomechanical Efectiveness

For each generated brace, the patient-specifc FEM simulated the standing out-of-brace position, the supine position with the nighttime brace, and the subsequent growth modulation for the expected treatment duration of 2 years. Standing out‑of‑brace simulation including gravitational loads (OOB) Te FEM initially created modeled the patient's standing geometry with no stresses acting on the anatomical structures. To determine the standing out-of-brace geometry under gravitational loads, as well as the patient's weightless geometry and the stabilizing muscular forces in the standing position, a previously described and validated method was employed and is briefy summarized here42. Upwards gravitational forces were applied to simulate weightlessness with additional stabilizing muscular forces acting antero-posteriorly and laterally on vertebrae T6, T10 and L3. Te resulting stresses were annulled, and downwards gravitational forces were then imposed. Te stabilizing muscular forces were automatically tuned so that the loaded standing spine geometry conformed to the patient's actual reconstructed spine. Afer solving, the standing loaded out-of-brace (OOB) patient geometry was obtained (Fig. 4). Nighttime in‑brace simulation in the supine position (IB)
To simulate nighttime bracing, the model previously described by Sattout et al. was refned30. Te weightless patient geometry was imported and defned in the supine position. A mattress was modeled underneath using a grid of hexahedral solid elements with material properties of polyurethane foam (E=0.3 MPa, ν=0.2)43,44. Te previously generated 3D model of the brace was added, modeled by hexahedral solid elements with the material properties of high-density polyethylene (E=1 GPa, ν=0.4) and a constant thickness of 4mm. Pairs of surface contact elements following the augmented Lagrangian formulation were created between the mattress and the skin, the internal surface of the brace and the skin, and the external surface of the brace and the top surface of the mattress. Gravitational forces were added, equivalent to the weight of the patient's trunk evenly distributed across vertebral gravitational centers. Te lateral and craniocaudal displacements of T1 and the pelvis were blocked, and the straps were tightened at 60N. Te model was solved using a nonlinear static solver with linearly interpolated loads using the unsymmetric Newton–Raphson method. Afer solving, the supine in-brace (IB) patient geometry was obtained (Fig. 4).

![5_image_0.png](5_image_0.png)

Figure 4. FE simulation of the two patient confgurations: on the lef, the standing out-of-brace position 

![5_image_1.png](5_image_1.png) under gravitational (G) loads (OOB, anterior view); on the right, the supine in-brace position (IB, lateral right view). Translucency was added to the skin elements to view the internal structures. Beam and spring elements representing internal sof tissues and connecting the torso skin to the skeleton were not shown for clarity. Growth simulation Stresses acting on each node composing the superior and inferior vertebral body epiphyseal growth plate of T2 to L5 were extracted from the two simulated confgurations (OOB and IB). To obtain the nodal stresses averaged over the treatment period (σ), the OOB stresses in the standing position (σOOB) and the IB stresses in the supine position (σIB) were combined in the following formula (Eq. 2), including a compliance factor (C) of 0.33 indicative of the proportion of time spent in-brace during sleep (8 h per day):

$$\mathbf{\tau}_{i}+\mathbf{C}*(\sigma_{I B}-\sigma_{0})$$
$f_d^+\\$ 4. 

$$({\mathfrak{I}})$$

σ = σOOB + C ∗ (σIB − σOOB) (2)

$\left(4\right)$. 
6
To quantify the asymmetrical stress distribution, these stresses were averaged on the lef (σL) and right (σR) 
sides of each growth plate. Calculations of the local growth rates in response to stresses were performed following the formula45:

(3)  GL = Gm(1 + β(σL − σm))
$\left(\begin{array}{l}G_{L}=G_{m}(1+\beta(\sigma_{L}-\sigma_{m}))\\ G_{R}=G_{m}(1+\beta(\sigma_{R}-\sigma_{m}))\end{array}\right)_{T2-L5\,growth\,plates}$
where GL is the longitudinal local growth rate applied on the lef side of the growth plate, GR on the right side, Gm is the baseline vertebral growth rate (0.8 mm/year for thoracic vertebrae, 1.1 mm/year for lumbar vertebrae)31, β is the documented vertebral bone stress sensitivity factor (1.5 MPa-1)45, and σm is the average stress on the entire growth plate.

From the initial unloaded standing out-of-brace patient geometry, an asymmetrical thermal expansion corresponding to the calculated growth rate GL and GR, multiplied by 2 years of treatment, was imposed on the lef and right nodes of each growth plate respectively. Afer solving, the out-of-brace 2-year post-growth (PG) patient geometry was obtained (Fig. 5).

Te FEM, including its immediate and post-growth simulations, was recently validated on a cohort of 35 patients following the rigorous ASME V&V40:2018 standard framework34. Te diference between the simulated 3D deformity metrics and the real clinical measurements were<6°, on the order of the measurement interoperator reproducibility.

## Objective Function

Te supine in-brace (IB) and out-of-brace 2-year post-growth (PG) spine geometries were used to calculate the optimization's objective function. To ensure an efective correction of the spine in the coronal and transverse planes while preventing fattening of the sagittal curves and favoring a normal alignment, metrics related to each anatomical plane of deformation were included in the objective function:
OF = WIB ∗ φIB + WPG ∗ φPG (4)
where OF is the objective function score, WIB and WPG are the weights factoring the simulated in-brace and post-growth confgurations (5 and 10). Te deformity terms φIB and φPG are calculated using the weighted sum:

![6_image_0.png](6_image_0.png)

![6_image_1.png](6_image_1.png)

![6_image_2.png](6_image_2.png)

Figure 5. FE simulation of growth: the OOB (top lef) and IB (bottom lef) nodal stresses acting on the vertebral epiphyseal growth plates are combined to determine the amount of thermal expansion (center) applied on the lef (red) and right (blue) nodes of each vertebral epiphyseal growth plate according to the growth rate formula (Eq. 3). Afer solving, the 2-year out-of-brace post-growth patient geometry is obtained (right). Closeups of the vertebral bodies of L2 and L3 are shown as examples. Other internal structures and posterior vertebral processes were not shown for clarity.

$$\left(5\right)$$
$$\phi_{sim}=W_{c}*\left(\left|\frac{\mathit{Cobb}_{MT,sim}}{\mathit{Cobb}_{MT,ini}}\right|+\left|\frac{\mathit{Cobb}_{TIL,sim}}{\mathit{Cobb}_{TIL,ini}}\right|\right)$$ $$+W_{s}*\left(\left|\frac{\mathit{ITK}_{sim}|-|\mathit{ITK}_{n}|}{|\mathit{ITK}_{ini}|-|\mathit{ITK}_{n}|}\right|+\left|\frac{|LL_{sim}|-|LL_{n}|}{|LL_{ini}|-|LL_{n}|}\right|\right)$$ $$+W_{t}*\left(\left|\frac{\mathit{AVR}_{MT,sim}}{\mathit{AVR}_{MT,ini}}\right|+\left|\frac{\mathit{AVR}_{TIL,sim}}{\mathit{AVR}_{TIL,ini}}\right|\right)$$
$$(6)$$
7
where sim is the simulated confguration (IB or PG), Cobb is the Cobb angle, ini is the initial value measured on the presenting deformity, MT is the main thoracic curve, TLL is the thoracolumbar/lumbar curve, TK is the thoracic kyphosis, LL is the lumbar lordosis, AVR is the average of the axial rotation of the curve's three most rotated vertebrae (apex±1 level), and Wc, Ws, Wt, are the weights factoring the coronal, sagittal and transverse alignment metrics respectively (2, 1 and 1). To penalize only the misaligned sagittal curves, the following values are afected to TKN and LLN46, based on their documented normal range47:

$\left\{\begin{array}{ll}20^{\circ}&\mbox{if$\mbox{TK}_{\rm sim}<20^{\circ}$}\\ \mbox{TK}_{\rm sim}&\mbox{if$20^{\circ}<\mbox{TK}_{\rm sim}<40^{\circ}$}\\ \mbox{40}^{\circ}&\mbox{if$\mbox{TK}_{\rm sim}>40^{\circ}$}\end{array}\right.$
$$L L_{m}$$
LLn = (6)  30◦
$$\epsilon=\left\{\begin{array}{l l}{{30^{\circ}}}&{{\mathrm{~if~LL_{s i m}<30^{\circ}~}}}\\ {{L L_{s i m}}}&{{\mathrm{~if~30^{\circ}<L L_{s i m}<60^{\circ}~}}}\\ {{60^{\circ}}}&{{\mathrm{~if~L L_{s i m}>60^{\circ}~}}}\end{array}\right.$$

## Optimization Process

As formulated, diminishing OF scores were linked to better biomechanical efectiveness according to generalized clinical objectives. Terefore, the optimization's goal was to fnd the global minimum of this OF score by modifying the ρ ofset vector controlling the brace topography. In addition, safety constraints related to the contact pressure between the brace and the skin were added to prevent braces designed too aggressively (maximum localized nodal contact pressure < 450 kPa, the documented threshold of barely perceptible pain in the MT & TL/L regions48). Iterations where the maximal in-brace contact pressure exceeded the set threshold were deemed invalid.

A surrogate optimization algorithm was used to carry out the optimization process49. Tis algorithm involves two main phases: constructing a surrogate and searching for a minimum. Initially, it generates random points within defned bounds and evaluates the objective function at these points to create a surrogate using a radial basis function interpolator. Ten, it searches for the function's minimum by sampling numerous points, evaluating a merit function using the surrogate, and choosing the best candidate for evaluation by the objective function. Tis adaptive point updates the surrogate for further iterations. Te algorithm balances between minimizing the surrogate and exploring new areas by adjusting the search scale and using diferent sampling methods.

Parameters including minimum surrogate points, grid size for brace patches and convergence criteria were tuned via experiments on test patient data, with the objective of striking a balance between search broadness, consistency and total solve time (<7 days): the surrogate was constructed with a minimum of 72 random points using the initial brace topography as seed, and it was stopped afer 500 iterations if convergence was reached (<5% OF score improvement over more than 50 iterations). If not, its execution was extended until convergence was attained, up to 1000 iterations.

## Brace Manufacturing And Clinical Evaluation

Figure 6 summarizes the entire design and manufacturing workfow. All optimal braces created by the algorithm were frst verifed and approved by the treating orthotist, then manufactured using their usual CAM approach: the uncut topography of the optimized brace was sent to a numerical milling machine to create its positive mold, and a 4mm thick high-density polyethylene sheet was thermoformed around it. Velcro straps were afxed at the locations set by the algorithm.

Te resulting braces were fnally ftted onto each patient at a clinical visit 3 weeks afer the initial one. If needed, minor faring and sanding of the brace's edges was performed by the orthotist to ensure comfort, but these modifcations did not afect the brace's topography. On the same day, an anteroposterior supine in-brace radiograph was acquired to measure the in-brace Cobb angle correction. To validate the design approach, the simulated correction was analyzed in 3D at each major step of the method and compared in the coronal plane to the actual in-brace correction. Finally, the predicted 3D correction afer 2 years of simulated growth was calculated and expected clinical outcomes were derived.

## Statistical Analyses

Comparison of 3D metrics was achieved using paired t tests, with a 0.05 signifcance level. Normality was verifed using Shapiro–Wilk tests, and homogeneity of variances for each pairwise comparison was verifed using F-tests. If normality was not demonstrated, non-parametric Wilcoxon signed-rank tests were used instead. All statistical analyses were performed in the Matlab environment (Matlab R2021a, MathWorks, Natick, MA, USA).

## Results

![7_Image_0.Png](7_Image_0.Png)

All recruited patients received an optimized brace, approved with no modifcations by the orthotist. All braces were well ftted and comfortable according to verbal testimonies of the orthotist and the patients. Te average hidden time for the algorithm to execute on a single personal computer was 136±28 h, or 5.7±1.2 days. Figure 7 shows an example of a typical patient's optimization results and the simulated in-brace correction compared to the actual one measured on the supine radiograph.

Figure 6. Complete design workfow repeated for all patients. From the standard clinical images, the patientspecifc FEM is created and used to evaluate the automatically generated brace shapes. Te design modifcations are guided by the optimization process aiming to minimize the OF score. Each brace generated by this method was verifed, manufactured and ftted on the patient. An antero-posterior in-brace supine radiograph was acquired on the same day.

![8_image_0.png](8_image_0.png)

![8_image_1.png](8_image_1.png)

Figure 7. Optimization graph (top center) showing the evolution of OF scores across the 500 optimization 

![8_image_2.png](8_image_2.png)

iterations following the surrogate optimization algorithm for a typical patient (bottom lef). Te resulting optimal brace (bottom center) was manufactured and ftted on the patient. Te simulated spine geometry was compared to the actual clinical radiograph (bottom right).

Table 1 presents the measured 3D deformity metrics at the presenting visit, measured or simulated values inside the optimal brace, and simulated afer 2 years. For all 17 patients, the initial presenting out-of-brace Cobb angles were 28°±8° (MT) and 31°±9° (TL/L) (Fig. 8). Donning the initial brace (pre-optimization) reduced the simulated in-brace Cobb angles to 19°±9° (MT) and 15°±6° (TL/L) (p < 0.0001). Donning the optimal brace (post-optimization) improved the correction to 13°±9° (MT) and 9°±6° (TL/L) (p<0.0001). Te actual Cobb angles measured on the patient's in-brace radiographs with the manufactured optimal brace were 9°±8° (MT) and 4°±5° (TL/L), corresponding to an actual in-brace correction of 70±28% (MT) and 90±15% (TL/L), or a main curve correction of 82±23%.

Te supine position fattened the sagittal curves at baseline, and adding the optimal brace in that position did not signifcantly modify the simulated TK; however, it improved the LL by+5°±3° (p<0.0001). In the transverse plane the simulated axial rotation of the MT apical vertebra was corrected by 2°±3° (p=0.036) but stayed unchanged for the TL/L apical vertebra (p>0.05).

Te post-growth out-of-brace simulations showed a non-signifcant average Cobb angle evolution of − 1°±8° 
(MT) and+1°±5° (TL/L). In 12 patients (71%), the deformity would improve or stabilize (±5°), while in the remainder cases it changed by less than 16% (MT) and 33% (TL/L).

## Discussion

Tis work describes a novel automated design method leveraging a patient's digital representation, able to create efective personalized braces from standard clinical images with no prior empirical biases. To our knowledge, it is the frst time a patient-specifc fnite element model was used to this extent for bespoke orthosis design in a 

|                         | Initial            | Immediate in-brace   | 2-year post growth   |
|-------------------------|--------------------|----------------------|----------------------|
| Cobb MT (°)             | 28±8 [17,44] (M)   | 9±8 [0, 22] (M)      | 27±15 [10,56] (S)    |
| Cobb TL/L (°)           | 31±9 [17,48] (M)   | 4±5 [0, 13] (M)      | 32±10 [16,52] (S)    |
| Toracic kyphosis (°)    | 27±11 [13,44] (M)  | 16±8 [3,33] (S)      | 28±10 [13,48] (S)    |
| Lumbar lordosis (°)     | 42±19 [16, 77] (M) | 37±15 [17, 67] (S)   | 44±23 [15, 91] (S)   |
| Axial rotation MT (°)   | 5±4 [1,16] (M)     | 3±3 [0, 10] (S)      | 6±5 [0, 19] (S)      |
| Axial rotation TL/L (°) | 8±7 [0, 22] (M)    | 8±7 [0, 21] (S)      | 8±7 [0, 23] (S)      |

Table 1. Initial, in-brace and 2-year deformity metrics, measured and simulated. Results are presented as mean±standard deviation [range]; values based on clinical radiographs measurements are indicated with a (M), values simulated using the FEM are indicated with a (S).

![9_image_0.png](9_image_0.png)

![9_image_1.png](9_image_1.png)

Figure 8. Cobb angle evolution for all patients: presenting out-of-brace deformity (blue), pre-optimization initial brace simulation (orange), post-optimization optimal brace simulation (yellow) and actual in-brace correction measured on the supine radiographs (purple). Negative values imply an over-correction. Statistically signifcant diferences from paired t tests are indicated with **(p<0.01) or ****(p<0.0001).

real clinical setting. Other groups have developed computer-assisted workfows for similar devices but have not incorporated the iterative evaluation of their biomechanical efects to guide design decisions50,51.

Braces created using our method were biomechanically efective. In-brace correction of the main scoliotic curve systematically exceeded the 50% correction threshold. Recent studies on nighttime bracing report average in-brace corrections ranging from 61 to 85%52,53, which puts our measured in-brace corrections in the upper portion of the range, or even higher. While an acceptable correction was achieved solely via the computationally inexpensive pre-optimization brace shape, the optimization process signifcantly improved the correction further and appears to be an essential step in the method. In 3D, transverse plane correction was limited compared to the coronal plane, as generally observed in other studies54,55, and sagittal curves were preserved inside a normal range as the brace-induced fatback efect was adequately avoided or even slightly improved for the lumbar lordosis. In a meta-analysis analyzing outcomes at the end of treatment, Buyuk et al. pooled nighttime bracing success rates 
(Cobb angle progression<5°) at 59%, lower than our simulated prediction of 71%13.

Immediate simulated corrections with the optimal brace were inside the clinically accepted threshold of the actual clinical radiographs (<5° average diference), but our FEM systematically underestimated the in-brace correction, especially in the TL/L region. Tis may be due to fexibility factors that were overestimated and need to be more fnely tuned to the patient's individual characteristics. Despite the diferences, the immediate simulation predictions were sensitive to brace topographical variations and the prediction ofsets did not signifcantly afect the diferential values used to guide the optimization process. Our model was therefore deemed valid for a comparative context of use like the one employed in this method.

In addition to immediate correction, the incorporated growth simulation provides information on how a specifc brace infuences the mechanisms of deformity correction over time. Tis represents an additional tool that can be used not only by the optimization process to account for long-term efects, but also by the clinical team to better prepare patients for treatment according to its expected evolution. In an analogous study, Cobetto et al. have shown that a growth model can be a powerful tool in assisting clinical decision-making and planning, leading to efective long-term results33.

While our immediate in-brace corrections were almost twice greater than the ones seen in full-time braces56, the reduced amount of prescribed daily wear limits the achievable efectiveness of the brace over longer treatments, as highlighted by our 2-year simulated outcomes. Tis prediction, however, does not include other rehabilitation activities that can be juxtaposed with the treatment's efect to increase longer-term efcacy. Nevertheless, brace-induced growth modulation is only active a third of the time, in a period where gravity has less impact on the deformity due to the supine position during sleep. Many questions remain on the performance of nighttime bracing only, and our initial post-growth predictions support the conclusion that higher levels of brace wear (more than 8 h/day), for instance by adding a component of daytime bracing, may need to be combined to our design workfow to achieve signifcant improvements in long-term outcomes6. In this sense, our method is easily adaptable to full-time braces, as only the in-brace simulation step needs to be simplifed to shif from the supine to the standing position.