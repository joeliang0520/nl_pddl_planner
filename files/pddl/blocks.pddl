;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;;; 4 op-blocks world
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;

(define (domain blocks)
    (:requirements :strips :typing)
    (:types
        blockA blocks - block
        robots  
        block - object
    )
    (:predicates
        (on ?x - block ?y - block)
        (ontable ?x - block)
        (clear ?x - block)
        (handfull)
        (holding ?x - block)
    )

    ; (:actions pickup putdown stack unstack)

    (:action pick-up
        :parameters (?x - block)
        :precondition (and
            ; (pickup ?x)
            (clear ?x)
            (ontable ?x)
            (not (handfull))
        )
        :effect (and
            (not (ontable ?x))
            (not (clear ?x))
            (handfull)
            (holding ?x)
        )
    )

    (:action put-down
        :parameters (?x - block)
        :precondition (and
            ; (putdown ?x)
            (holding ?x)
            (handfull)
        )
        :effect (and
            (not (holding ?x))
            (clear ?x)
            (not (handfull))
            (ontable ?x))
    )

    (:action stack
        :parameters (?x - block ?y - block)
        :precondition (and
            ; (stack ?x ?y)
            (holding ?x)
            (clear ?y)
            (handfull)
        )
        :effect (and
            (not (holding ?x))
            (not (clear ?y))
            (clear ?x)
            (not (handfull))
            (on ?x ?y)
        )
    )

    (:action unstack
        :parameters (?x - block ?y - block)
        :precondition (and
            ; (unstack ?x)
            (on ?x ?y)
            (clear ?x)
            (not (handfull))
        )
        :effect (and
            (holding ?x)
            (clear ?y)
            (not (clear ?x))
            (handfull)
            (not (on ?x ?y))
        )
    )
)