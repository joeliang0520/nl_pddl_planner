;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; 4 op-blocks world
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (domain blocks)
    (:requirements :strips :typing)
    (:types
        blockA blocks - block
        robots - robot
        block - object
    )
    (:predicates
        (on ?x - block ?y - block)
        (ontable ?x - block)
        (clear ?x - block)
        (handfull ?x - robot)
        (holding ?x - block)
    )

    ; (:actions pickup putdown stack unstack)

    (:action pick-up
        :parameters (?x - block ?robot - robot)
        :precondition (and
            ; (pickup ?x)
            (clear ?x)
            (ontable ?x)
            (not (handfull ?robot))
        )
        :effect (and
            (not (ontable ?x))
            (not (clear ?x))
            (handfull ?robot)
            (holding ?x)
        )
    )

    (:action put-down
        :parameters (?x - block ?robot - robot)
        :precondition (and
            ; (putdown ?x)
            (holding ?x)
            (handfull ?robot)
        )
        :effect (and
            (not (holding ?x))
            (clear ?x)
            (not (handfull ?robot))
            (ontable ?x))
    )

    (:action stack
        :parameters (?x - block ?y - block ?robot - robot)
        :precondition (and
            ; (stack ?x ?y)
            (holding ?x)
            (clear ?y)
            (handfull ?robot)
        )
        :effect (and
            (not (holding ?x))
            (not (clear ?y))
            (clear ?x)
            (not (handfull ?robot))
            (on ?x ?y)
        )
    )

    (:action unstack
        :parameters (?x - block ?y - block ?robot - robot)
        :precondition (and
            ; (unstack ?x)
            (on ?x ?y)
            (clear ?x)
            (not (handfull ?robot))
        )
        :effect (and
            (holding ?x)
            (clear ?y)
            (not (clear ?x))
            (handfull ?robot)
            (not (on ?x ?y))
        )
    )
)