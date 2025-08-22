

(define (problem logistics)
    (:domain logistics-strips)
    (:objects
        t0 t1 - truck
        p0 p1 - obj
        toronto ottawa - loc
        ; a0 a1 a2 a3 a4 c0 c1 c2 t0 l20 p0 p1
        )
    (:init
        (at t0 ottawa)
        (at t1 toronto)
        (at p0 ottawa)
        ; (at p1 l10)
        ; (at a0 l00)
        ; (at a1 l10)
        ; (at a2 l00)
        ; (at a3 l00)
        ; (at a4 l20)
    )
    (:goal
        (and
            (at p0 toronto)
            (at p1 ottawa))
    )
)