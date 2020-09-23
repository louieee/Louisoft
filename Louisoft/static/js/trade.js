const position = document.getElementById('position')
const submit = document.getElementById('button')
const stoploss = document.getElementById('stoploss')
const entry = document.getElementById('entry')
const stake = document.getElementById('stake')
const profit = document.getElementById('profit')
const form = document.getElementById('trade_form')
const result = document.getElementById('result')


const return_ = () =>{
    result.className = 'd-none'
    form.classList.replace('d-none', "d-block")
}

const display = () =>{
    let exit_tp
    let exit_sl
    if (position.value == '+') {
        exit_tp = Number(entry.value) + (profit.value / stake.value)
        exit_sl = Math.abs(Number(entry.value) - (stoploss.value / stake.value))
    } else if (position.value == '-') {
        exit_tp = Math.abs(Number(entry.value) - (profit.value / stake.value))
        exit_sl = Number(entry.value) + (stoploss.value / stake.value)
    }
    form.classList.replace('d-block', 'd-none')
    result.className = 'd-block'
    tp = document.getElementById('tp')
    sl = document.getElementById('sl')
    tp.innerText = exit_tp
    sl.innerText = exit_sl
}