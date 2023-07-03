import { LemonButton } from '@posthog/lemon-ui'
import { useActions, useValues } from 'kea'
import { SupportModal } from 'lib/components/Support/SupportModal'
import { supportLogic } from 'lib/components/Support/supportLogic'
import { IconBugShield } from 'lib/lemon-ui/icons'

export function SupportModalButton({ name, email }: { name?: string; email?: string }): JSX.Element | null {
    const { openSupportLoggedOutForm } = useActions(supportLogic)
    const { isSupportFormAvailable } = useValues(supportLogic)

    return isSupportFormAvailable ? ( // We don't provide support for self-hosted instances
        <>
            <div className="text-center">
                <LemonButton
                    onClick={() => {
                        openSupportLoggedOutForm(name, email, null, 'login')
                    }}
                    status="stealth"
                    icon={<IconBugShield />}
                    size="small"
                >
                    <span className="text-muted">Report an issue</span>
                </LemonButton>
            </div>
            <SupportModal loggedIn={false} />
        </>
    ) : null
}
