(define (domain logistics-strips)
    (:requirements :strips :typing)
    (:types
        truck1 - truck
        obj truck airplane city airport loc
    ) ; default object

    (:predicates
        (at ?obj - obj ?loc - loc)
        (in ?obj1 - obj ?obj2 - obj)
    )

    (:action LOAD-TRUCK1
        :parameters (?obj - obj ?truck - truck1 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK1
        :parameters (?obj - obj ?truck - truck1 ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK1
        :parameters (?truck - truck1 ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )
)