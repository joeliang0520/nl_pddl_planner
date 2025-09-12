(define (domain blocksworld-4ops-ssa)
  (:requirements :strips)
  (:predicates (clear ?x)
               (ontable ?x)
               (handempty)
               (holding ?x)
               (on ?x ?y))

  (:action pick-up
    :parameters (?ob)
    :precondition (and)
    :effect (and (holding ?ob)
                 (not (clear ?ob))
                 (not (ontable ?ob))
                 (not (handempty))))

  (:action put-down
    :parameters  (?ob)
    :precondition (and)
    :effect (and (clear ?ob)
                 (handempty)
                 (ontable ?ob)
                 (not (holding ?ob))))

  (:action stack
    :parameters  (?ob ?underob)
    :precondition (and)
    :effect (and (handempty)
                 (clear ?ob)
                 (on ?ob ?underob)
                 (not (clear ?underob))
                 (not (holding ?ob))))

  (:action unstack
    :parameters  (?ob ?underob)
    :precondition (and)
    :effect (and (holding ?ob)
                 (clear ?underob)
                 (not (on ?ob ?underob))
                 (not (clear ?ob))
                 (not (handempty)))))