# Stage-level execution priority

User direction supersedes continued long GPT-Direct sweeps. Direct remains a
bounded recovery/reference option, not the main execution strategy. Native task
success, recovery and experience reuse remain the objective; this does not replace
them with a smaller motion-only goal.

## Next sequence

- [x] Capture idealized RGB-D and calibrated camera poses without object-state queries.
- [x] Add strict visible-surface deprojection, rejecting invalid/mixed neighborhoods.
- [ ] Verify spatial agreement across views and robot geometry before control use.
- [ ] Establish robot-only finger geometry; do not mistake the hand origin for contact.
- [ ] One sensor-grounded approach with local feedback, action/time bounds, progress
  checks and termination on rejection or unexpected changes. Keep execution receipts.
- [ ] Inspect arrival once, then attempt grasp/lift and independently verify effect.
- [ ] Qualify FLUX before using it as an alternative local executor. Reviewing every
  short FLUX chunk with GPT is not sufficient to meet the call-efficiency objective.
- [ ] Continue alignment/insertion, recovery and successful-trace reuse after capture.

Target: one to a few GPT calls per uncomplicated stage (approach, grasp/lift,
alignment/insertion). Report actual calls, executed actions, simulated/wall time,
cost and physical stage completion. A lower call count without progress is failure.
Do not silently lengthen open-loop sequences, relax limits, or claim collision
safety from target-point depth. Local monitoring must run between bounded chunks.

## Measurement evidence and limits

On the retained capture, the measured hand frame projects to approximately
(94.46, 3.56) in the left image, consistent with its visible location. This is a
coarse visual sanity check, not independent quantitative calibration validation.

An operator-selected card-surface pixel (158,216) in the original 640x360 left
image deprojects to world (0.260935,-0.358056,0.099727) m. Optical depth is
1.256487 m and the 5x5 neighborhood range is 0.017708 m. Identity selection was
manual visual inspection, not autonomous model discovery. No object transform
or semantic simulator ID was used. This is a visible surface point, NOT a grasp
center, obstacle-free waypoint, or measured statistical confidence interval.
No motion was commanded from it. The helper keeps observation identity attached.

112 CPU tests pass. They establish software checks, not successful approach,
calibration accuracy or manipulation. No additional API calls were made.
