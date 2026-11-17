"""Capacity allocation, not dimensional packing or a carrier quote engine."""
from datetime import date
import math
import time


def positive(value, label, zero=False):
    try:
        v = float(value)
    except (ValueError, TypeError):
        raise ValueError(f'{label} must be numeric') from None
    if not math.isfinite(v) or v > 1e12 or (v < 0 if zero else v <= 0):
        raise ValueError(f'{label} must be finite, at most 1e12, and {"nonnegative" if zero else "positive"}')
    return v


def validate_jobs(rows):
    if not rows or len(rows) > 500:
        raise ValueError('Provide 1 to 500 jobs')
    result, seen = [], set()
    for row in rows:
        ident = str(row['job_id']).strip()
        if not ident or ident.lower() in ('nan', 'none') or ident in seen:
            raise ValueError('Job IDs must be nonempty and unique')
        seen.add(ident)
        result.append(dict(job_id=ident, weight_kg=positive(row['weight_kg'], 'Weight'),
                           volume_m3=positive(row['volume_m3'], 'Volume'),
                           priority=positive(row.get('priority', 1), 'Priority')))
    return result


def validate_rates(rows):
    clean = []
    for row in rows:
        r = dict(row)
        for field in ('min_kg', 'max_kg', 'min_m3', 'max_m3', 'amount'):
            r[field] = positive(r[field], field, zero=True)
        if r['max_kg'] < r['min_kg'] or r['max_m3'] < r['min_m3']:
            raise ValueError('Rate maxima must be >= minima')
        if r['basis'] not in ('per trip', 'per tonne', 'per m³'):
            raise ValueError('Unknown rate basis')
        if not all(str(r.get(k, '')).strip().lower() not in ('', 'nan', 'none') for k in ('currency', 'origin', 'destination', 'source', 'included_charges')):
            raise ValueError('Rates need currency, route, source and included charges')
        try:
            start, end = date.fromisoformat(str(r['valid_from'])), date.fromisoformat(str(r['valid_until']))
        except ValueError:
            raise ValueError('Rate dates must use YYYY-MM-DD') from None
        if end < start:
            raise ValueError('Rate end must be >= start')
        r['valid_from'], r['valid_until'] = start.isoformat(), end.isoformat()
        for key in ('currency', 'origin', 'destination', 'source', 'included_charges'):
            r[key] = str(r[key]).strip()
        clean.append(r)
    return clean


def price_load(weight, volume, rates, shipment_date, origin, destination):
    """Ambiguous, expired, unmatched, or wrong-route prices are never free."""
    matches = [r for r in rates if r['min_kg'] <= weight <= r['max_kg'] and
               r['min_m3'] <= volume <= r['max_m3'] and
               r['valid_from'] <= shipment_date <= r['valid_until'] and
               r['origin'].strip().casefold() == origin.strip().casefold() and
               r['destination'].strip().casefold() == destination.strip().casefold()]
    if len(matches) != 1:
        return {'amount': None, 'currency': None, 'status': 'unpriced' if not matches else 'ambiguous rates'}
    r = matches[0]
    multiplier = {'per trip': 1, 'per tonne': weight / 1000, 'per m³': volume}[r['basis']]
    return {'amount': round(r['amount'] * multiplier, 2), 'currency': r['currency'], 'status': 'estimate',
            'source': r['source'], 'included_charges': r['included_charges']}


def allocate(rows, max_kg, max_m3, rates=(), shipment_date=None, origin='', destination=''):
    from ortools.linear_solver import pywraplp
    max_kg, max_m3 = positive(max_kg, 'Payload'), positive(max_m3, 'Volume')
    jobs, rates = validate_jobs(rows), validate_rates(rates)
    shipment_date = shipment_date or date.today().isoformat()
    date.fromisoformat(shipment_date)
    unassigned = [dict(j, reason='Exceeds working payload or volume') for j in jobs if j['weight_kg'] > max_kg or j['volume_m3'] > max_m3]
    remaining = [j for j in jobs if j['weight_kg'] <= max_kg and j['volume_m3'] <= max_m3]
    loads = []
    deadline = time.monotonic() + 15
    while remaining:
        if time.monotonic() >= deadline:
            unassigned.extend(dict(j, reason='Planning time budget reached; retry remaining jobs') for j in remaining)
            break
        solver = pywraplp.Solver.CreateSolver('SCIP')
        if solver is None:
            raise RuntimeError('SCIP solver unavailable')
        solver.SetTimeLimit(1000)
        x = [solver.BoolVar(f'job_{i}') for i in range(len(remaining))]
        solver.Add(solver.Sum(j['weight_kg'] * x[i] for i, j in enumerate(remaining)) <= max_kg)
        solver.Add(solver.Sum(j['volume_m3'] * x[i] for i, j in enumerate(remaining)) <= max_m3)
        solver.Maximize(solver.Sum(j['priority'] * (j['weight_kg']/max_kg + j['volume_m3']/max_m3) * x[i] for i,j in enumerate(remaining)))
        status = solver.Solve()
        if status not in (solver.OPTIMAL, solver.FEASIBLE):
            unassigned.extend(dict(j, reason='Solver did not find a feasible load within time limit') for j in remaining)
            break
        picked = [i for i,v in enumerate(x) if v.solution_value() > .5]
        if not picked:
            unassigned.extend(dict(j, reason='No selection found') for j in remaining)
            break
        chosen = [remaining[i] for i in picked]
        weight, volume = sum(j['weight_kg'] for j in chosen), sum(j['volume_m3'] for j in chosen)
        if weight > max_kg + 1e-5 or volume > max_m3 + 1e-7:
            raise RuntimeError('Solver result exceeded capacity')
        loads.append(dict(jobs=chosen, weight_kg=weight, volume_m3=volume,
                          solver_status='optimal for this load' if status == solver.OPTIMAL else 'feasible (time limit)',
                          price=price_load(weight,volume,rates,shipment_date,origin,destination)))
        remaining = [j for i,j in enumerate(remaining) if i not in set(picked)]
    return {'loads': loads, 'unassigned': unassigned}
