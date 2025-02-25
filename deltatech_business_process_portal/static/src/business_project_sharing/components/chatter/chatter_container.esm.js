/** @odoo-module */

import {formatDateTime, parseDateTime} from "@web/core/l10n/dates";
import {useService} from "@web/core/utils/hooks";
import {sprintf} from "@web/core/utils/strings";
import {ChatterComposer} from "./chatter_composer.esm";
import {ChatterMessageCounter} from "./chatter_message_counter.esm";
import {ChatterMessages} from "./chatter_messages.esm";
import {ChatterPager} from "./chatter_pager.esm";

const {Component, markup, onWillStart, useState, onWillUpdateProps} = owl;

export class ChatterContainer extends Component {
    setup() {
        this.rpc = useService("rpc");
        this.state = useState({
            currentPage: this.props.pagerStart,
            messages: [],
            options: this.defaultOptions,
        });

        onWillStart(this.onWillStart);
        onWillUpdateProps(this.onWillUpdateProps);
    }

    get defaultOptions() {
        return {
            message_count: 0,
            is_user_public: true,
            is_user_employee: false,
            is_user_published: false,
            display_composer: Boolean(this.props.resId),
            partner_id: null,
            pager_scope: 4,
            pager_step: 10,
        };
    }

    get options() {
        return this.state.options;
    }

    set options(options) {
        this.state.options = {
            ...this.defaultOptions,
            ...options,
            display_composer: Boolean(options.display_composer),
            access_token: typeof options.display_composer === "string" ? options.display_composer : "",
        };
    }

    get composerProps() {
        return {
            allowComposer: Boolean(this.props.resId),
            displayComposer: this.state.options.display_composer,
            partnerId: this.state.options.partner_id || undefined,
            token: this.state.options.access_token,
            resModel: this.props.resModel,
            resId: this.props.resId,
            BusinessProjectSharingId: this.props.BusinessProjectSharingId,
            postProcessMessageSent: async () => {
                this.state.currentPage = 1;
                await this.fetchMessages();
            },
            attachments: this.state.options.default_attachment_ids,
        };
    }

    onWillStart() {
        this.initChatter(this.messagesParams(this.props));
    }

    onWillUpdateProps(nextProps) {
        this.initChatter(this.messagesParams(nextProps));
    }

    async onChangePage(page) {
        this.state.currentPage = page;
        await this.fetchMessages();
    }

    async initChatter(params) {
        if (params.res_id && params.res_model) {
            const chatterData = await this.rpc("/mail/chatter_init", params);
            this.state.messages = this.preprocessMessages(chatterData.messages);
            this.options = chatterData.options;
        } else {
            this.state.messages = [];
            this.options = {};
        }
    }

    async fetchMessages() {
        const result = await this.rpc("/mail/chatter_fetch", this.messagesParams(this.props));
        this.state.messages = this.preprocessMessages(result.messages);
        this.state.options.message_count = result.message_count;
        return result;
    }

    messagesParams(props) {
        const params = {
            res_model: props.resModel,
            res_id: props.resId,
            limit: this.state.options.pager_step,
            offset: (this.state.currentPage - 1) * this.state.options.pager_step,
            allow_composer: Boolean(props.resId),
            business_project_sharing_id: props.BusinessProjectSharingId,
        };
        if (props.token) {
            params.token = props.token;
        }
        if (props.domain) {
            params.domain = props.domain;
        }
        return params;
    }

    preprocessMessages(messages) {
        return messages.map((m) => ({
            ...m,
            author_avatar_url: sprintf("/web/image/mail.message/%s/author_avatar/50x50", m.id),
            published_date_str: sprintf(
                this.env._t("Published on %s"),
                formatDateTime(parseDateTime(m.date, {format: "MM-dd-yyy HH:mm:ss"}))
            ),
            body: markup(m.body),
        }));
    }

    updateMessage(message_id, changes) {
        Object.assign(
            this.state.messages.find((m) => m.id === message_id),
            changes
        );
    }
}

ChatterContainer.components = {
    ChatterComposer,
    ChatterMessageCounter,
    ChatterMessages,
    ChatterPager,
};

ChatterContainer.props = {
    token: {type: String, optional: true},
    resModel: String,
    resId: {type: Number, optional: true},
    pid: {type: String, optional: true},
    hash: {type: String, optional: true},
    pagerStart: {type: Number, optional: true},
    twoColumns: {type: Boolean, optional: true},
    BusinessProjectSharingId: {type: Number, optional: true},
};
ChatterContainer.defaultProps = {
    token: "",
    pid: "",
    hash: "",
    pagerStart: 1,
};
ChatterContainer.template = "deltatech_business_process_portal.ChatterContainer";
