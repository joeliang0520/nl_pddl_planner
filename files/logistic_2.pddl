(define (domain logistics-strips)
    (:requirements :strips :typing)
    (:types
        obj truck airplane city airport loc
    ) ; default object

    (:predicates
        (OBJ ?obj - obj)
        (TRUCK ?truck - truck)
        (LOCATION ?loc - loc)
        (AIRPLANE ?airplane - airplane)
        (CITY ?city - city)
        (AIRPORT ?airport - airport)
        (at ?obj - obj ?loc - loc)
        (in ?obj1 - obj ?obj2 - obj)
        (in-city ?obj - obj ?city - city)
    )

    (:action LOAD-TRUCK
        :parameters (?obj - obj ?truck - truck ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (at ?obj ?loc))
        :effect (and (not (at ?obj ?loc)) (in ?obj ?truck))
    )

    (:action UNLOAD-TRUCK
        :parameters (?obj - obj ?truck - truck ?loc - loc)
        :precondition (and
            (at ?truck ?loc) (in ?obj ?truck))
        :effect (and (not (in ?obj ?truck)) (at ?obj ?loc))
    )

    (:action DRIVE-TRUCK
        :parameters (?truck - truck ?from - loc ?to - loc)
        :precondition (and
            (at ?truck ?from))
        :effect (and (not (at ?truck ?from)) (at ?truck ?to))
    )

)