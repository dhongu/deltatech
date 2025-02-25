/** @odoo-module */

const {Component} = owl;

export class ChatterMessageCounter extends Component {}

ChatterMessageCounter.props = {
    count: Number,
};
ChatterMessageCounter.template = "deltatech_business_process_portal.ChatterMessageCounter";
